# NOTES

Public finding log for this plugin. No internal information.

- The implementation is pinned to `waldur-site-agent==1.0.6rc19`, matching
  `docs/CONTRACT.md` from `waldur-multicloud` tag `contract-v1`.
- `hcloud==2.23.0` returns Action objects for create, delete, shutdown, and
  power-on. Every mutation is waited with a configured finite retry count;
  adoption also has a bounded server-state poll.
- `waldur-resource-uuid` is the deterministic ownership/adoption label.
  Hetzner names are unique within a project but are not treated as identity.
- A provider 404 during lookup or deletion is treated as successful absence.
- The SDK performs bounded retries for transport errors, selected gateway
  responses, conflicts, and rate limits. No unbounded plugin retry is added.
- Hetzner Cloud has no user/project membership model in this plugin scope, so
  membership associations, per-user limits, and username synchronization are
  intentionally unsupported no-ops.
- No reliable billing-period usage mapping is defined by the contract;
  reporting returns an empty report rather than inventing accounting units.
- Server flavor/image changes and attached-volume/network lifecycle are not
  implemented because no corresponding provider mapping is specified by the
  vendored contract.
