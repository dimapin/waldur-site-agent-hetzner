# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.12.7@sha256:95f2aa1fe59274951cfe9b0cbc7972e879ff1004bc8945d130a32eb0dbd85945 AS uv

FROM python:3.12-slim@sha256:09f7da3bc104798d0afb40bc08d23ab2da20a76130cec1f2ef170848f5d85217 AS builder
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY waldur_site_agent_hetzner ./waldur_site_agent_hetzner
RUN uv sync --system-certs --frozen --no-dev --no-editable

FROM python:3.12-slim@sha256:09f7da3bc104798d0afb40bc08d23ab2da20a76130cec1f2ef170848f5d85217 AS runtime
ENV PATH="/app/.venv/bin:/usr/local/bin:/usr/bin:/bin" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY --from=builder --chown=10001:10001 /app/.venv /app/.venv
USER 10001:10001
ENTRYPOINT ["waldur_site_agent"]
CMD ["--mode", "order_process", "--config-file", "/etc/waldur/config.yaml"]
