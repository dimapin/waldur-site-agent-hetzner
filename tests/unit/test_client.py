from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from hcloud import APIException, HCloudException
from requests.exceptions import Timeout
from waldur_site_agent.backend.exceptions import BackendError

from waldur_site_agent_hetzner.client import WALDUR_UUID_LABEL, HetznerClient


@pytest.fixture
def sdk():
    value = Mock()
    value.servers = Mock()
    return value


@pytest.fixture
def client(sdk):
    return HetznerClient(
        "very-secret-token",
        server_type="cx22",
        image="ubuntu-24.04",
        action_max_retries=3,
        poll_interval=0.001,
        sdk_client=sdk,
    )


def server(server_id=42, status="running"):
    return SimpleNamespace(
        id=server_id,
        name="waldur-server",
        status=status,
        labels={WALDUR_UUID_LABEL: "uuid"},
        server_type=None,
        location=None,
        public_net=None,
    )


def test_create_labels_and_waits_for_all_actions(client, sdk):
    primary, followup = Mock(), Mock()
    sdk.servers.create.return_value = SimpleNamespace(
        server=server(),
        action=primary,
        next_actions=[followup],
        root_password="ignored",
    )
    result = client.create_server(
        resource_uuid="123e4567-e89b-12d3-a456-426614174000",
        name="waldur-123",
        project="project-a",
    )
    assert result.id == 42
    kwargs = sdk.servers.create.call_args.kwargs
    assert kwargs["labels"][WALDUR_UUID_LABEL] == "123e4567-e89b-12d3-a456-426614174000"
    primary.wait_until_finished.assert_called_once_with(max_retries=3)
    followup.wait_until_finished.assert_called_once_with(max_retries=3)


def test_wait_failure_is_sanitized(client):
    action = Mock()
    action.wait_until_finished.side_effect = HCloudException("provider timeout")
    with pytest.raises(BackendError, match="server creation") as error:
        client._wait(action, "server creation")
    assert "very-secret-token" not in str(error.value)


def test_wait_transport_failure_is_sanitized(client):
    action = Mock()
    action.wait_until_finished.side_effect = Timeout("provider timeout")
    with pytest.raises(BackendError, match="server creation") as error:
        client._wait(action, "server creation")
    assert "provider timeout" not in str(error.value)


def test_ping_transport_failure_is_sanitized(client, sdk):
    sdk.servers.get_list.side_effect = Timeout("provider timeout")
    with pytest.raises(BackendError, match="health check") as error:
        client.ping()
    assert "provider timeout" not in str(error.value)


def test_lookup_404_is_absent(client, sdk):
    sdk.servers.get_by_id.side_effect = APIException(404, "not found", {})
    assert client.get_resource(99) is None


def test_delete_404_after_lookup_is_success(client, sdk):
    sdk.servers.get_by_id.return_value = server()
    sdk.servers.delete.side_effect = APIException(404, "not found", {})
    assert client.delete_resource("42") == "42"


def test_duplicate_adoption_labels_are_rejected(client, sdk):
    sdk.servers.get_all.return_value = [server(1), server(2)]
    with pytest.raises(BackendError, match="Multiple"):
        client.find_by_waldur_uuid("uuid")


def test_adoption_wait_is_bounded(client, sdk, monkeypatch):
    sdk.servers.get_by_id.return_value = server(status="initializing")
    sleep = Mock()
    monkeypatch.setattr("waldur_site_agent_hetzner.client.time.sleep", sleep)
    with pytest.raises(BackendError, match="Timed out"):
        client.wait_server_stable("42")
    assert sdk.servers.get_by_id.call_count == 3
    assert sleep.call_count == 2


def test_repr_does_not_contain_token(client):
    assert "very-secret-token" not in repr(client)
