# AGENTS.md — waldur-site-agent-hetzner

> **Status: EXPERIMENT.** Öffentlicher Versuch, Fortführung offen.
> Keine Produktionsnutzung. Kein offizielles Waldur-Projekt.

Dieses Repo enthält genau EIN Waldur-Site-Agent-Plugin:
**hetzner** (SDK: `hcloud`). Repo-übergreifende
Regeln, Contract und Testkit liegen im Meta-Repo `waldur-multicloud` —
dessen AGENTS.md gilt hier mit, insbesondere Public-Repo-Hygiene,
Definition of Done und Verbote.

## Verankerung (bei jedem Arbeitspaket prüfen)

| Was | Wert | Regel |
|---|---|---|
| Core | `waldur-site-agent==<PIN>` (PyPI, 1.x) | Bump nur nach Contract-Diff im Meta-Repo |
| Contract | docs/CONTRACT.md, vendored vom Meta-Repo-Tag `contract-vN` | Tag steht im Delegations-Prompt und im Dateikopf; Abweichung oder veraltet → STOPP |
| Testkit | uv-Git-Dependency auf Meta-Repo-**Tag** | nie auf main pinnen |
| Provider-Doku | docs/PROVIDER_NOTES.md (vendored aus Meta docs/providers/) | Drift zum Meta-Stand ist ein Review-Befund |

## Struktur

```
waldur_site_agent_hetzner/
├── backend.py        # Backend-Klasse gegen Contract
├── client.py         # dünner API/SDK-Wrapper
tests/
├── unit/             # Rolle: provider-implementer (Mocks, Fehlerpfade)
└── acceptance/       # Rolle: test-engineer — Implementer: NICHT anfassen
```

Contract-Tests kommen aus dem Testkit und laufen hier parametrisiert
mit — sie werden in diesem Repo weder erstellt noch geändert.
CODEOWNERS erzwingt Review auf tests/acceptance/.

## Nicht verhandelbar (Kurzfassung aus dem Meta-Repo)

- **Idempotenz:** Create prüft per deterministischem Tag/Label
  (Waldur-UUID), ob die Ressource existiert → adoptieren statt
  duplizieren. Terminate auf 404 == Erfolg. backend_id sofort nach
  Create an Waldur melden; das Crash-Fenster dazwischen ist
  testpflichtig.
- **Async-Semantik:** Eine Operation ist erst fertig, wenn der
  Provider den Zielzustand bestätigt — "Request abgeschickt" ist kein
  Erfolg. Das konkrete Muster steht in docs/PROVIDER_NOTES.md.
- **Fehlerpfad:** Jeder Order-Fehler wird in Waldur sichtbar
  (Order-State + Meldung), nicht nur im Log. Keine leeren excepts,
  kein Retry ohne Obergrenze. Secrets nie loggen (__repr__ prüfen).
- **Scope:** Änderungen nur in diesem Repo. Braucht ein Arbeitspaket
  Contract- oder Testkit-Änderungen → Blocker melden, Meta-Repo-MR,
  nicht lokal umgehen.

## Kommandos

```bash
uv sync
uv run pytest -m "not e2e"
uvx prek run --all-files
uv run pytest -m e2e      # nur lokal/dispatch, echte Credentials via Env
```

CI: .github/workflows/ci.yml (Push/PR: Lint + Tests ohne e2e),
.github/workflows/e2e.yml (nur workflow_dispatch, Environment `e2e`,
TTL-getaggte Ressourcen, Cleanup per Tag-Suche auch bei Abbruch).

## Rollen

Kanon: Meta-Repo docs/agents/. Rollenänderungen zuerst dort, dann in
die Wrapper kopieren:
- `.claude/agents/*.md` — Claude Code (Subagent-Delegation)
- `.github/agents/*.agent.md` — GitHub Copilot (VS Code Agent-Picker
  bzw. Zuweisung an den Copilot Coding Agent)

VS Code liest diese AGENTS.md zusätzlich als Always-on-Instruktionen —
eine separate copilot-instructions.md ist deshalb nicht nötig.
