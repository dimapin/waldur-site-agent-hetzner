# Hetzner Cloud (`hcloud`)
- Mutationen liefern Action-Objekte mit Status; SDK bietet
  wait_until_finished. Erfolg == Action abgeschlossen, nicht Request
  abgeschickt.
- Rate-Limits: Header auswerten, Backoff mit Obergrenze.
- Idempotenz-Anker: Labels (Waldur-Resource-UUID als Label), Namen
  sind NICHT eindeutig erzwungen.
- Kein Nutzer-/Projektmodell im Plugin-Scope → membership_sync
  voraussichtlich nicht anwendbar; Befund in NOTES.md dokumentieren.
