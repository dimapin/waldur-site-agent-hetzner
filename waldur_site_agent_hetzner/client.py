"""Thin, synchronous wrapper around hcloud-python."""

from __future__ import annotations

import time
from typing import Any

from hcloud import APIException, Client, HCloudException
from hcloud.images import Image
from hcloud.locations import Location
from hcloud.server_types import ServerType
from hcloud.servers import BoundServer
from hcloud.ssh_keys import SSHKey
from waldur_site_agent.backend.clients import BaseClient
from waldur_site_agent.backend.exceptions import BackendError
from waldur_site_agent.backend.structures import Association, ClientResource

WALDUR_UUID_LABEL = "waldur-resource-uuid"
WALDUR_PROJECT_LABEL = "waldur-project"


def _is_not_found(exc: APIException) -> bool:
    return str(exc.code) == "404"


class HetznerClient(BaseClient):
    """HCloud operations with bounded waits and sanitized failures."""

    def __init__(
        self,
        token: str,
        *,
        server_type: str,
        image: str,
        location: str | None = None,
        ssh_keys: list[str] | None = None,
        user_data: str | None = None,
        api_endpoint: str = "https://api.hetzner.cloud/v1",
        timeout: float = 30.0,
        poll_interval: float = 1.0,
        action_max_retries: int = 120,
        labels: dict[str, str] | None = None,
        sdk_client: Client | None = None,
    ) -> None:
        self.server_type = server_type
        self.image = image
        self.location = location
        self.ssh_keys = list(ssh_keys or [])
        self.user_data = user_data
        self.labels = dict(labels or {})
        self.action_max_retries = action_max_retries
        self.poll_interval = poll_interval
        self._client = sdk_client or Client(
            token=token,
            api_endpoint=api_endpoint,
            application_name="waldur-site-agent-hetzner",
            poll_interval=poll_interval,
            poll_max_retries=action_max_retries,
            timeout=timeout,
        )
        self.api_endpoint = api_endpoint

    def __repr__(self) -> str:
        return f"HetznerClient(api_endpoint={self.api_endpoint!r})"

    @staticmethod
    def _failure(operation: str, exc: HCloudException) -> BackendError:
        code = getattr(exc, "code", "provider_error")
        return BackendError(f"Hetzner {operation} failed (code: {code})")

    def _wait(self, action: Any, operation: str) -> None:
        try:
            action.wait_until_finished(max_retries=self.action_max_retries)
        except HCloudException as exc:
            raise self._failure(operation, exc) from exc

    def ping(self) -> bool:
        try:
            self._client.servers.get_list(page=1, per_page=1)
        except HCloudException as exc:
            raise self._failure("health check", exc) from exc
        return True

    def _server_by_id(self, resource_id: str) -> BoundServer | None:
        try:
            numeric_id = int(resource_id)
        except (TypeError, ValueError) as exc:
            raise BackendError("Hetzner resource ID must be numeric") from exc
        try:
            return self._client.servers.get_by_id(numeric_id)
        except APIException as exc:
            if _is_not_found(exc):
                return None
            raise self._failure("server lookup", exc) from exc
        except HCloudException as exc:
            raise self._failure("server lookup", exc) from exc

    def find_by_waldur_uuid(self, resource_uuid: str) -> BoundServer | None:
        try:
            servers = self._client.servers.get_all(
                label_selector=f"{WALDUR_UUID_LABEL}={resource_uuid}"
            )
        except HCloudException as exc:
            raise self._failure("adoption lookup", exc) from exc
        if len(servers) > 1:
            raise BackendError(
                "Multiple Hetzner servers carry the same Waldur resource UUID label"
            )
        return servers[0] if servers else None

    @staticmethod
    def _as_resource(server: BoundServer) -> ClientResource:
        labels = server.labels or {}
        return ClientResource(
            name=server.name or str(server.id),
            description=server.name or "",
            organization=labels.get(WALDUR_PROJECT_LABEL, ""),
            backend_id=str(server.id),
        )

    def list_resources(self) -> list[ClientResource]:
        try:
            servers = self._client.servers.get_all(label_selector=WALDUR_UUID_LABEL)
        except HCloudException as exc:
            raise self._failure("server listing", exc) from exc
        return [self._as_resource(server) for server in servers]

    def get_resource(self, resource_id: str) -> ClientResource | None:
        server = self._server_by_id(resource_id)
        return self._as_resource(server) if server else None

    def get_server(self, resource_id: str) -> BoundServer | None:
        return self._server_by_id(resource_id)

    def wait_server_stable(self, resource_id: str) -> BoundServer:
        """Wait until an adopted server reaches a terminal usable state."""
        for attempt in range(self.action_max_retries):
            server = self._server_by_id(resource_id)
            if server is None:
                raise BackendError("Adopted Hetzner server disappeared")
            if server.status in {"running", "off"}:
                return server
            if server.status in {"deleting", "unknown"}:
                raise BackendError("Adopted Hetzner server is not usable")
            if attempt + 1 < self.action_max_retries:
                time.sleep(self.poll_interval)
        raise BackendError("Timed out waiting for adopted Hetzner server")

    def create_server(
        self, *, resource_uuid: str, name: str, project: str
    ) -> BoundServer:
        labels = {
            **self.labels,
            WALDUR_UUID_LABEL: resource_uuid,
            WALDUR_PROJECT_LABEL: project,
        }
        kwargs: dict[str, Any] = {
            "name": name,
            "server_type": ServerType(name=self.server_type),
            "image": Image(name=self.image),
            "labels": labels,
            "ssh_keys": [SSHKey(name=item) for item in self.ssh_keys],
            "user_data": self.user_data,
        }
        if self.location:
            kwargs["location"] = Location(name=self.location)
        try:
            response = self._client.servers.create(**kwargs)
            self._wait(response.action, "server creation")
            for action in response.next_actions:
                self._wait(action, "server creation follow-up")
            return response.server
        except BackendError:
            raise
        except HCloudException as exc:
            raise self._failure("server creation", exc) from exc

    def create_resource(
        self,
        name: str,
        description: str,
        organization: str,
        parent_name: str | None = None,
    ) -> str:
        del description, parent_name
        server = self.create_server(
            resource_uuid=name,
            name=f"waldur-{name.replace('-', '')}"[:63],
            project=organization,
        )
        return str(server.id)

    def delete_resource(self, name: str) -> str:
        server = self._server_by_id(name)
        if server is None:
            return name
        try:
            action = self._client.servers.delete(server)
            self._wait(action, "server deletion")
        except APIException as exc:
            if _is_not_found(exc):
                return name
            raise self._failure("server deletion", exc) from exc
        except BackendError:
            raise
        except HCloudException as exc:
            raise self._failure("server deletion", exc) from exc
        return name

    def stop_server(self, resource_id: str) -> bool:
        server = self._server_by_id(resource_id)
        if server is None:
            raise BackendError("Hetzner server does not exist")
        if server.status == "off":
            return True
        try:
            self._wait(self._client.servers.shutdown(server), "server shutdown")
        except HCloudException as exc:
            raise self._failure("server shutdown", exc) from exc
        return True

    def start_server(self, resource_id: str) -> bool:
        server = self._server_by_id(resource_id)
        if server is None:
            raise BackendError("Hetzner server does not exist")
        if server.status == "running":
            return True
        try:
            self._wait(self._client.servers.power_on(server), "server power-on")
        except HCloudException as exc:
            raise self._failure("server power-on", exc) from exc
        return True

    def metadata(self, resource_id: str) -> dict[str, Any]:
        server = self._server_by_id(resource_id)
        if server is None:
            return {}
        public_net = getattr(server, "public_net", None)
        ipv4 = getattr(getattr(public_net, "ipv4", None), "ip", None)
        ipv6 = getattr(getattr(public_net, "ipv6", None), "ip", None)
        return {
            "name": server.name,
            "status": server.status,
            "server_type": getattr(server.server_type, "name", None),
            "location": getattr(server.location, "name", None),
            "ipv4": ipv4,
            "ipv6": ipv6,
        }

    def set_resource_limits(
        self, resource_id: str, limits_dict: dict[str, int]
    ) -> None:
        del resource_id, limits_dict

    def get_resource_limits(self, resource_id: str) -> dict[str, int]:
        del resource_id
        return {}

    def get_resource_user_limits(self, resource_id: str) -> dict[str, dict[str, int]]:
        del resource_id
        return {}

    def set_resource_user_limits(
        self, resource_id: str, username: str, limits_dict: dict[str, int]
    ) -> str:
        del resource_id, username, limits_dict
        return ""

    def get_association(self, user: str, resource_id: str) -> Association | None:
        del user, resource_id
        return None

    def create_association(
        self, username: str, resource_id: str, default_account: str | None = None
    ) -> str:
        del username, resource_id, default_account
        return ""

    def delete_association(self, username: str, resource_id: str) -> str:
        del username, resource_id
        return ""

    def get_usage_report(
        self, resource_ids: list[str], timezone: str | None = None
    ) -> list[Any]:
        del resource_ids, timezone
        return []

    def list_resource_users(self, resource_id: str) -> list[str]:
        del resource_id
        return []
