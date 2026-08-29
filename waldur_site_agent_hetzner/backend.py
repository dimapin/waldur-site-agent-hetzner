"""Waldur backend implementation for Hetzner Cloud servers."""

from __future__ import annotations

import re
from typing import Any

from pydantic import Field, SecretStr, ValidationError, field_validator
from waldur_site_agent.backend.backends import BaseBackend
from waldur_site_agent.backend.exceptions import BackendError, ConfigurationError
from waldur_site_agent.backend.structures import BackendResourceInfo
from waldur_site_agent.common.plugin_schemas import PluginBackendSettingsSchema

from .client import HetznerClient

_LABEL_KEY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,61}[A-Za-z0-9]$|^[A-Za-z0-9]$")
_RESERVED_LABELS = {"waldur-resource-uuid", "waldur-project"}


class HetznerBackendSettingsSchema(PluginBackendSettingsSchema):
    """Validated settings; SecretStr keeps credentials out of repr/errors."""

    token: SecretStr = Field(min_length=1)
    server_type: str = Field(min_length=1, max_length=64)
    image: str = Field(min_length=1, max_length=128)
    location: str | None = Field(default=None, min_length=1, max_length=64)
    ssh_keys: list[str] = Field(default_factory=list)
    user_data: SecretStr | None = Field(default=None, max_length=32768)
    api_endpoint: str = "https://api.hetzner.cloud/v1"
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    poll_interval_seconds: float = Field(default=1.0, gt=0, le=30)
    action_max_retries: int = Field(default=120, ge=1, le=3600)
    soft_delete: bool = False
    labels: dict[str, str] = Field(default_factory=dict)

    @field_validator("token", "server_type", "image", "location")
    @classmethod
    def reject_surrounding_whitespace(cls, value: Any) -> Any:
        raw = value.get_secret_value() if isinstance(value, SecretStr) else value
        if raw is not None and raw != raw.strip():
            raise ValueError("must not have surrounding whitespace")
        return value

    @field_validator("api_endpoint")
    @classmethod
    def secure_endpoint(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("must use HTTPS")
        return value.rstrip("/")

    @field_validator("ssh_keys")
    @classmethod
    def valid_ssh_keys(cls, values: list[str]) -> list[str]:
        if any(not item or item != item.strip() for item in values):
            raise ValueError("SSH key names must be non-empty and trimmed")
        if len(values) != len(set(values)):
            raise ValueError("SSH key names must be unique")
        return values

    @field_validator("labels")
    @classmethod
    def valid_labels(cls, labels: dict[str, str]) -> dict[str, str]:
        if _RESERVED_LABELS.intersection(labels):
            raise ValueError("Waldur ownership labels are reserved")
        for key, value in labels.items():
            if not _LABEL_KEY.fullmatch(key) or (
                value and not _LABEL_KEY.fullmatch(value)
            ):
                raise ValueError("invalid Hetzner label")
        return labels


class HetznerBackend(BaseBackend):
    """Provision and manage one Hetzner server per Waldur resource."""

    supports_cycle_preflight = True

    def __init__(
        self, backend_settings: dict, backend_components: dict[str, dict]
    ) -> None:
        try:
            settings = HetznerBackendSettingsSchema.model_validate(backend_settings)
        except ValidationError as exc:
            fields = sorted(
                {".".join(map(str, error["loc"])) for error in exc.errors()}
            )
            raise ConfigurationError(
                f"Invalid Hetzner backend settings: {', '.join(fields)}"
            ) from None
        super().__init__(
            settings.model_dump(exclude={"token", "user_data"}), backend_components
        )
        self.backend_type = "hetzner"
        self.settings = settings
        self.client = HetznerClient(
            settings.token.get_secret_value(),
            server_type=settings.server_type,
            image=settings.image,
            location=settings.location,
            ssh_keys=settings.ssh_keys,
            user_data=(
                settings.user_data.get_secret_value() if settings.user_data else None
            ),
            api_endpoint=settings.api_endpoint,
            timeout=settings.timeout_seconds,
            poll_interval=settings.poll_interval_seconds,
            action_max_retries=settings.action_max_retries,
            labels=settings.labels,
        )

    def ping(self, raise_exception: bool = False) -> bool:
        try:
            return self.client.ping()
        except BackendError:
            if raise_exception:
                raise
            return False

    def diagnostics(self) -> bool:
        return self.ping()

    def list_components(self) -> list[str]:
        return []

    def _get_usage_report(self, resource_backend_ids: list[str]) -> dict:
        del resource_backend_ids
        return {}

    @staticmethod
    def _resource_uuid(waldur_resource: Any) -> str:
        value = str(getattr(waldur_resource, "uuid", "")).lower()
        if not re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value
        ):
            raise BackendError("Waldur resource UUID is missing or invalid")
        return value

    @staticmethod
    def _server_name(resource_uuid: str) -> str:
        return f"waldur-{resource_uuid.replace('-', '')}"

    def create_resource(
        self, waldur_resource: Any, user_context: dict | None = None
    ) -> BackendResourceInfo:
        resource_uuid = self._resource_uuid(waldur_resource)
        existing = self.client.find_by_waldur_uuid(resource_uuid)
        if existing is not None:
            server = self.client.wait_server_stable(str(existing.id))
            return BackendResourceInfo(
                backend_id=str(server.id),
                backend_metadata=self.client.metadata(str(server.id)),
            )
        self._pre_create_resource(waldur_resource, user_context)
        try:
            server = self.client.create_server(
                resource_uuid=resource_uuid,
                name=self._server_name(resource_uuid),
                project=waldur_resource.project_slug,
            )
        except BackendError:
            existing = self.client.find_by_waldur_uuid(resource_uuid)
            if existing is None:
                raise
            server = self.client.wait_server_stable(str(existing.id))
        info = BackendResourceInfo(
            backend_id=str(server.id),
            backend_metadata=self.client.metadata(str(server.id)),
        )
        self.post_create_resource(info, waldur_resource, user_context)
        return info

    def delete_resource(self, waldur_resource: Any, **kwargs: str) -> None:
        del kwargs
        resource_id = str(getattr(waldur_resource, "backend_id", ""))
        if not resource_id.strip() or self.client.get_resource(resource_id) is None:
            return None
        self._pre_delete_resource(waldur_resource)
        if self.settings.soft_delete:
            self.client.stop_server(resource_id)
        else:
            self.client.delete_resource(resource_id)
        self.post_delete_resource(waldur_resource)
        return None

    def downscale_resource(self, resource_backend_id: str) -> bool:
        return self.client.stop_server(resource_backend_id)

    def pause_resource(self, resource_backend_id: str) -> bool:
        return self.client.stop_server(resource_backend_id)

    def restore_resource(self, resource_backend_id: str) -> bool:
        return self.client.start_server(resource_backend_id)

    def get_resource_metadata(self, resource_backend_id: str) -> dict:
        return self.client.metadata(resource_backend_id)

    def _collect_resource_limits(
        self, waldur_resource: Any
    ) -> tuple[dict[str, int], dict[str, int]]:
        del waldur_resource
        return {}, {}

    def _pre_create_resource(
        self, waldur_resource: Any, user_context: dict | None = None
    ) -> None:
        del waldur_resource, user_context
