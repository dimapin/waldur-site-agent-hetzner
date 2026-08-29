from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from waldur_site_agent.backend.exceptions import BackendError, ConfigurationError

from waldur_site_agent_hetzner.backend import (
    HetznerBackend,
    HetznerBackendSettingsSchema,
)

UUID = "123e4567-e89b-12d3-a456-426614174000"


def settings(**updates):
    values = {
        "token": "super-secret",
        "server_type": "cx22",
        "image": "ubuntu-24.04",
        "action_max_retries": 2,
    }
    values.update(updates)
    return values


def resource(backend_id=""):
    return SimpleNamespace(
        uuid=UUID,
        name="My VM",
        slug="my-vm",
        project_slug="project-a",
        backend_id=backend_id,
        limits={},
    )


def test_settings_reject_insecure_endpoint_without_leaking_token():
    with pytest.raises(ConfigurationError) as error:
        HetznerBackend(settings(api_endpoint="http://invalid"), {})
    assert "api_endpoint" in str(error.value)
    assert "super-secret" not in str(error.value)


def test_settings_repr_redacts_secrets():
    parsed = HetznerBackendSettingsSchema.model_validate(
        settings(user_data="secret cloud init")
    )
    assert "super-secret" not in repr(parsed)
    assert "secret cloud init" not in repr(parsed)


def test_settings_reject_reserved_label():
    with pytest.raises(ConfigurationError):
        HetznerBackend(settings(labels={"waldur-resource-uuid": "mine"}), {})


def test_create_adopts_by_uuid_without_creating():
    backend = HetznerBackend(settings(), {})
    client = Mock()
    found = SimpleNamespace(id=17)
    client.find_by_waldur_uuid.return_value = found
    client.wait_server_stable.return_value = found
    client.metadata.return_value = {"status": "running"}
    backend.client = client
    result = backend.create_resource(resource())
    assert result.backend_id == "17"
    client.create_server.assert_not_called()
    client.find_by_waldur_uuid.assert_called_once_with(UUID)


def test_create_uses_deterministic_name_and_label():
    backend = HetznerBackend(settings(), {})
    client = Mock()
    client.find_by_waldur_uuid.return_value = None
    client.create_server.return_value = SimpleNamespace(id=18)
    client.metadata.return_value = {}
    backend.client = client
    result = backend.create_resource(resource())
    assert result.backend_id == "18"
    client.create_server.assert_called_once_with(
        resource_uuid=UUID,
        name="waldur-123e4567e89b12d3a456426614174000",
        project="project-a",
    )


def test_create_recovers_crash_window_by_adoption():
    backend = HetznerBackend(settings(), {})
    client = Mock()
    adopted = SimpleNamespace(id=19)
    client.find_by_waldur_uuid.side_effect = [None, adopted]
    client.create_server.side_effect = BackendError("timed out")
    client.wait_server_stable.return_value = adopted
    client.metadata.return_value = {}
    backend.client = client
    assert backend.create_resource(resource()).backend_id == "19"


def test_create_propagates_failure_without_adoptable_server():
    backend = HetznerBackend(settings(), {})
    client = Mock()
    client.find_by_waldur_uuid.side_effect = [None, None]
    client.create_server.side_effect = BackendError("safe failure")
    backend.client = client
    with pytest.raises(BackendError, match="safe failure"):
        backend.create_resource(resource())


def test_delete_empty_id_is_noop_and_delete_delegates():
    backend = HetznerBackend(settings(), {})
    backend.client = Mock()
    backend.delete_resource(resource())
    backend.client.delete_resource.assert_not_called()
    backend.delete_resource(resource("42"))
    backend.client.delete_resource.assert_called_once_with("42")


def test_lifecycle_delegates_to_client():
    backend = HetznerBackend(settings(), {})
    backend.client = Mock()
    backend.client.stop_server.return_value = True
    backend.client.start_server.return_value = True
    assert backend.pause_resource("42")
    assert backend.downscale_resource("42")
    assert backend.restore_resource("42")
    assert backend.client.stop_server.call_count == 2
    backend.client.start_server.assert_called_once_with("42")


def test_invalid_resource_uuid_fails_before_api_call():
    backend = HetznerBackend(settings(), {})
    backend.client = Mock()
    with pytest.raises(BackendError, match="UUID"):
        backend.create_resource(SimpleNamespace(uuid="bad"))
    backend.client.find_by_waldur_uuid.assert_not_called()
