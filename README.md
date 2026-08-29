# Waldur Site Agent for Hetzner Cloud

> **EXPERIMENT** — This is not an official Waldur or Hetzner project and is
> not intended for production use yet.

A `waldur-site-agent` backend that provisions Hetzner Cloud servers. It
supports idempotent creation/adoption, deletion, pause/downscale, restore,
metadata reporting, and provider health checks.

## Configuration

```yaml
offerings:
  - name: hetzner
    waldur_api_url: https://waldur.example.com/api/
    waldur_api_token: replace-me
    waldur_offering_uuid: 123e4567-e89b-12d3-a456-426614174000
    backend_type: hetzner
    order_processing_backend: hetzner
    backend_settings:
      token: replace-me
      server_type: cx22
      image: ubuntu-24.04
      location: fsn1
      ssh_keys: [operations]
      action_max_retries: 120
      poll_interval_seconds: 1
      timeout_seconds: 30
      labels:
        managed-by: waldur
    backend_components: {}
```

`token` and optional `user_data` are secret-aware fields and are excluded from
client representations and validation errors. The API endpoint must use HTTPS.
The labels `waldur-resource-uuid` and `waldur-project` are reserved. The former
is the stable adoption key; server names are deterministic and are not used as
identity.

## Development

```bash
uv sync
uv run pytest -m "not e2e"
uvx prek run --all-files
helm lint charts/waldur-site-agent-hetzner
helm template test charts/waldur-site-agent-hetzner
```

## Container and Helm

The multi-stage image runs as UID/GID 10001 and contains no build tooling. The
chart disables service-account token mounting, drops Linux capabilities, and
uses a read-only root filesystem. Create a Secret containing the complete
configuration before installation:

```bash
kubectl create secret generic waldur-site-agent-hetzner \
  --from-file=config.yaml=/secure/path/config.yaml
helm upgrade --install hetzner charts/waldur-site-agent-hetzner
```

See [AGENTS.md](AGENTS.md) for contribution rules, [the vendored
contract](docs/CONTRACT.md), and [provider notes](docs/PROVIDER_NOTES.md).
