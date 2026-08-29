# Waldur Site Agent – Provider-Contract

## Referenzstand

- **Upstream:** `waldur/waldur-site-agent`. (Quellanker: `pyproject.toml:1-6` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- **Commit:** `0cb51a188850aeccde9fdca94cfae41cb707b7b6`. (Quellanker: `pyproject.toml:1-6` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- **Core:** `1.0.6rc19`, Python `>=3.9.2,<4.0`. (Quelle: `pyproject.toml:1-6` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- **API-Modelle:** `waldur-api-client==8.1.0rc19.dev20260730123512`. (Quelle: `pyproject.toml:14-25` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- Vollständige Definitionen der importierten API-Modelle sind im Core-Repository **NICHT GEFUNDEN**; `OfferingUser`, `OrderDetails`, `Project` und `Resource` kommen aus `waldur_api_client`. (Quelle: `waldur_site_agent/backend/backends.py:10-15` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

## 1. Plugin-Registrierung

| Zweck | Entry-Point-Gruppe | Ladecontract |
|---|---|---|
| Provider | `waldur_site_agent.backends` | Wert wird als `type[BaseBackend]` geladen. (Quelle: `waldur_site_agent/common/utils.py:124-131` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| Username | `waldur_site_agent.username_management_backends` | Wert wird als `type[AbstractUsernameManagementBackend]` geladen. (Quelle: `waldur_site_agent/common/utils.py:133-140` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| Komponenten-Schema | `waldur_site_agent.component_schemas` | Nur Unterklassen von `PluginComponentSchema`. (Quelle: `waldur_site_agent/common/plugin_schemas.py:110-132` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| Settings-Schema | `waldur_site_agent.backend_settings_schemas` | Nur Unterklassen von `PluginBackendSettingsSchema`. (Quelle: `waldur_site_agent/common/plugin_schemas.py:135-159` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |

Das TOML-Format ist `name = "modul:Klasse"`. DigitalOcean verwendet denselben Namen in allen drei Provider-Gruppen. (Quelle: `plugins/digitalocean/pyproject.toml:20-29` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

OpenNebula bestätigt das Format mit `opennebula = "waldur_site_agent_opennebula.backend:OpenNebulaBackend"`. (Quelle: `plugins/opennebula/pyproject.toml:22-24` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Ein Paket darf mehrere Namen exportieren; CSCS-DWDI exportiert drei Backendklassen. (Quelle: `plugins/cscs-dwdi/pyproject.toml:20-24` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Der Loader instanziiert exakt mit `(offering.backend_settings, offering.backend_components_dict)`; unbekannte Namen ergeben `UnknownBackend()` und Version `unknown`. (Quelle: `waldur_site_agent/common/utils.py:576-608` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

## 2. Backend-Interfaces

### 2.1 `BaseBackend`

`BaseBackend(ABC)` ist die abstrakte Providerbasis. Der vollständige Konstruktor folgt. (Quelle: `waldur_site_agent/backend/backends.py:39-40,118-133` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

```python
def __init__(
    self,
    backend_settings: dict,
    backend_components: dict[str, dict],
) -> None
```

Er hält Settings, Komponenten, Client, Service-Provider-UUID, Zeitzone und Offering-Partitionen. (Quelle: `waldur_site_agent/backend/backends.py:39-40,118-133` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Eine konkrete Klasse muss diese zehn abstrakten Signaturen implementieren. (Quelle: `waldur_site_agent/backend/backends.py:135-325,491-514,826-848` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

| Signatur | Contract |
|---|---|
| `ping(self, raise_exception: bool = False) -> bool` | Leichter Healthcheck; bei angefordertem Raise `BackendError`, sonst `False`; ohne Mechanismus `False`. (Quelle: `waldur_site_agent/backend/backends.py:135-151` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `diagnostics(self) -> bool` | Diagnose loggen und Status liefern; ohne Unterstützung `True`. Keine Exception dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:168-181` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `list_components(self) -> list[str]` | Komponentenbezeichner oder ohne Discovery `[]`. Keine Exception dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:183-196` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `_get_usage_report(self, resource_backend_ids: list[str]) -> dict` | Standardreport in Waldur-Einheiten oder `{}`. Keine Exception dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:198-227` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `downscale_resource(self, resource_backend_id: str) -> bool` | Erfolg `True`; ohne Feature ebenfalls `True`. Keine Exception dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:256-272` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `pause_resource(self, resource_backend_id: str) -> bool` | Erfolg `True`; ohne Feature ebenfalls `True`. Keine Exception dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:274-289` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `restore_resource(self, resource_backend_id: str) -> bool` | Erfolg `True`; ohne Feature ebenfalls `True`. Keine Exception dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:291-306` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `get_resource_metadata(self, resource_backend_id: str) -> dict` | Metadaten oder `{}`. Keine Exception dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:308-325` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `_collect_resource_limits(self, waldur_resource: WaldurResource) -> tuple[dict[str, int], dict[str, int]]` | `(backend_limits, waldur_limits)`; `backend = waldur * unit_factor`; ohne Limits `({}, {})`. Keine Exception dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:491-514` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `_pre_create_resource(self, waldur_resource: WaldurResource, user_context: Optional[dict] = None) -> None` | Voraussetzungen herstellen; Fehler als `BackendError`; ohne Vorbereitung `pass`. (Quelle: `waldur_site_agent/backend/backends.py:826-848` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |

`create_resource(self, waldur_resource: WaldurResource, user_context: Optional[dict] = None) -> BackendResourceInfo` ist konkret: ID aus `resource.slug`, dann Delegation an `create_resource_with_id`. (Quelle: `waldur_site_agent/backend/backends.py:805-824` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

`create_resource_with_id` ruft Pre-Hook, Backend-Create, Limit-Setup und Post-Hook auf; eine vorhandene ID erzeugt `DuplicateResourceError`, Create-Fehler sind als `BackendError` dokumentiert. (Quelle: `waldur_site_agent/backend/backends.py:850-894` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

`delete_resource(self, waldur_resource: WaldurResource, **kwargs: str) -> Optional[str]` überspringt leere oder fehlende Ressourcen, unterstützt `soft_delete`, ruft Vor- und Nach-Hook und liefert synchron `None`; ein Async-Override darf eine Order-UUID liefern. (Quelle: `waldur_site_agent/backend/backends.py:684-753` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

`set_resource_limits(self, resource_backend_id: str, limits: dict[str, int]) -> Optional[str]` konvertiert per `unit_factor`, delegiert an den Client und liefert synchron `None`; ein Async-Override darf eine Order-UUID liefern. (Quelle: `waldur_site_agent/backend/backends.py:1146-1163` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

### 2.2 Capabilities und Order-Hooks

Standardmäßig `False` sind `supports_decreasing_usage`, `supports_async_orders`, `supports_resource_api_keys`, `supports_cycle_preflight`, `supports_user_homedirs`, `supports_periodic_settings`, `requires_source_project` und `shared_project_membership`; Team-Retry ist `1` Versuch mit `3.0` Sekunden Abstand, behandelte Zustände sind `OK` und `ERRED`. (Quelle: `waldur_site_agent/backend/backends.py:42-116` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Bei `supports_cycle_preflight=True` läuft `run_preflight()` einmal je Offering-Zyklus; `BackendNotReadyError` überspringt den Zyklus. (Quelle: `waldur_site_agent/common/processors.py:855-876` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

`check_pending_order(self, order_backend_id: str) -> bool` liefert standardmäßig `True`; Async-Backends liefern `False` für laufend und werfen `BackendError` für fehlgeschlagen oder abgebrochen. (Quelle: `waldur_site_agent/backend/backends.py:349-365` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

`evaluate_pending_order(self, order: OrderDetails, waldur_rest_client: AuthenticatedClient) -> PendingOrderDecision` liefert standardmäßig `ACCEPT`; Alternativen sind `REJECT` und `PENDING`. (Quelle: `waldur_site_agent/backend/backends.py:31-36,367-394` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

### 2.3 `BaseClient`

Für die Standardpfade sind folgende abstrakt markierte Signaturen definiert. (Quelle: `waldur_site_agent/backend/clients.py:41-225` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

```python
def list_resources(self) -> list[ClientResource]
def get_resource(self, resource_id: str) -> Optional[ClientResource]
def create_resource(self, name: str, description: str, organization: str,
                    parent_name: Optional[str] = None) -> str
def delete_resource(self, name: str) -> str
def set_resource_limits(self, resource_id: str,
                        limits_dict: dict[str, int]) -> Optional[str]
def get_resource_limits(self, resource_id: str) -> dict[str, int]
def get_resource_user_limits(self, resource_id: str) -> dict[str, dict[str, int]]
def set_resource_user_limits(self, resource_id: str, username: str,
                             limits_dict: dict[str, int]) -> str
def get_association(self, user: str, resource_id: str) -> Optional[Association]
def create_association(self, username: str, resource_id: str,
                       default_account: Optional[str] = None) -> str
def delete_association(self, username: str, resource_id: str) -> str
def get_usage_report(self, resource_ids: list[str],
                     timezone: Optional[str] = None) -> list
def list_resource_users(self, resource_id: str) -> list[str]
```

(Quelle: `waldur_site_agent/backend/clients.py:41-225` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Schreiboperationen dokumentieren `BackendError`; `get_resource` signalisiert Abwesenheit mit `None`. (Quelle: `waldur_site_agent/backend/clients.py:50-110,136-198` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

### 2.4 Username-Backend

`AbstractUsernameManagementBackend(ABC)` nimmt `backend_settings: dict | None = None` und `offering: Optional[Offering] = None`. (Quelle: `waldur_site_agent/backend/backends.py:1298-1326` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

```python
def generate_username(self, offering_user: OfferingUser) -> str
def get_username(self, offering_user: OfferingUser) -> Optional[str]
```

Beide Methoden sind abstrakt. (Quelle: `waldur_site_agent/backend/backends.py:1328-1334` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Benötigte Benutzeraktionen werden mit `OfferingUserAccountLinkingRequiredError` oder `OfferingUserAdditionalValidationRequiredError` signalisiert; beide tragen Nachricht und optionale `comment_url`. (Quelle: `waldur_site_agent/backend/backends.py:1298-1311` und `waldur_site_agent/backend/exceptions.py:14-39` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

## 3. Datenstrukturen

| Typ | Felder |
|---|---|
| `ClientResource` | `name`, `description`, `organization`, `backend_id`: jeweils `str = ""`. (Quelle: `waldur_site_agent/backend/structures.py:6-14` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `Association` | `account: str = ""`, `user: str = ""`, `value: int = 0`. (Quelle: `waldur_site_agent/backend/structures.py:16-23` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |
| `BackendResourceInfo` | Stringfelder `backend_id`, `parent_id`, `effective_id`, `pending_order_id`; Factory-Felder `users`, `usage`, `limits`, `backend_metadata`, `endpoints`. (Quelle: `waldur_site_agent/backend/structures.py:25-39` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`) |

Core übernimmt nach Create aus `BackendResourceInfo` die Backend-ID und optional Limits, Metadaten und Endpoints nach Waldur. (Quelle: `waldur_site_agent/common/processors.py:1182-1246` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

### Resource und Order

Eigene vollständige Core-Dataclasses für Waldur `Resource` und `Order` sind **NICHT GEFUNDEN**; verwendet werden externe `Resource` und `OrderDetails`. (Quelle: `waldur_site_agent/backend/backends.py:10-15` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Generisches Provisioning liest mindestens `slug`, `project_slug`, `name`, `backend_id` und `limits` aus `Resource`. (Quelle: `waldur_site_agent/backend/backends.py:805-824,850-900` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Der Processor verwendet zusätzlich `uuid` für Backend-ID, Limits, Metadaten und Endpoints. (Quelle: `waldur_site_agent/common/processors.py:1190-1242` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Für Orders liest Core `uuid`, `resource_name`, `type_` und `state`; verarbeitet werden CREATE/RESTORE, UPDATE und TERMINATE. (Quelle: `waldur_site_agent/common/processors.py:950-1040` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Der Approval-Hook nennt außerdem `project_uuid`, `customer_uuid`, `created_by_*`, `attributes` sowie Consumer- und Provider-Nachrichten. (Quelle: `waldur_site_agent/backend/backends.py:367-386` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

### Usage

```python
{
    "<resource_backend_id>": {
        "TOTAL_ACCOUNT_USAGE": {"<component>": value},
        "<username>": {"<component>": value},
    }
}
```

`TOTAL_ACCOUNT_USAGE` ist erforderlich; Komponentenkeys entsprechen `backend_components`; Werte sind nach `unit_factor` bereits Waldur-Einheiten. (Quelle: `waldur_site_agent/backend/backends.py:198-226` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

`get_usage_report_for_period(resource_backend_ids, year, month, waldur_resource=None) -> dict` liefert standardmäßig `{}`; dann werden historische Perioden übersprungen. (Quelle: `waldur_site_agent/backend/backends.py:229-254` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

### Komponenten

`AccountingType` ist exakt `USAGE="usage"`, `LIMIT="limit"`, `ONE_TIME="one"`. (Quelle: `waldur_site_agent/common/structures.py:34-40` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

`BackendComponent` erlaubt Zusatzfelder. Pflicht sind `measured_unit`, `accounting_type`, `label`; Defaults sind `unit_factor=1.0`, `unit_factor_reporting=None`, `limit=None`. (Quelle: `waldur_site_agent/common/structures.py:63-85` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Optionale Marketplace-Felder sind `description`, Min/Max/Default-Limits, `limit_period`, `article_code`, Boolean/Prepaid sowie Min/Max/Step für Prepaid- und Renewal-Dauer. (Quelle: `waldur_site_agent/common/structures.py:86-121` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

## 4. Konfiguration

### Offering

Pflicht sind `name`, `waldur_api_url`, `waldur_offering_uuid`, `backend_type`; Token ist standardmäßig leer, Settings und Komponenten sind leere Mappings. (Quelle: `waldur_site_agent/common/structures.py:173-194` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Authentifizierung verlangt entweder `waldur_api_token` oder gemeinsam `oidc_token_url`, `oidc_client_id`, `oidc_client_secret`. (Quelle: `waldur_site_agent/common/structures.py:178-185,236-247` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

```yaml
backend_type: provider-name
order_processing_backend: provider-name # Optional[str], Default ""
membership_sync_backend: provider-name  # Optional[str], Default ""
reporting_backend: provider-name        # Optional[str], Default ""
username_management_backend: base       # str, Default "base"
```

(Quelle: `waldur_site_agent/common/structures.py:187-194,208-218` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Plugin-Schemas werden anhand von `backend_type`, nicht anhand der Rollenfelder gewählt. (Quelle: `waldur_site_agent/common/structures.py:540-568` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Schemafehler werden nur geloggt; Core verwendet danach unvalidierte Daten. Konstruktorvalidierung bleibt daher erforderlich. (Quelle: `waldur_site_agent/common/plugin_schemas.py:162-209,212-240` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Weitere Offering-Felder umfassen STOMP/TLS sowie `resource_import_enabled=False`, `username_reconciliation_enabled=False`, `verify_ssl=True`, `omit_anomalous_usage_components=False`. (Quelle: `waldur_site_agent/common/structures.py:196-234` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

### Root

Root enthält `offerings`, optionale Sentry- und APM-URLs, `timezone="UTC"`, `global_proxy=""`, `log_level="INFO"`, `reporting_periods=2` im Bereich 1–12, `expose_backend_error_details=True` und `log_shipping`. (Quelle: `waldur_site_agent/common/structures.py:462-500` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

## 5. Fehler, Wiederholung und Kollision

Definiert sind `BackendError`, `ConfigurationError`, zwei OfferingUser-Aktionsfehler, `BackendNotReadyError` und `DuplicateResourceError`; letzterer erbt von `BackendError`. (Quelle: `waldur_site_agent/backend/exceptions.py:1-54` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Vor Provisionierungsbeginn lässt `BackendNotReadyError` die Order für den nächsten Zyklus stehen; andere frühe Fehler lassen sie ebenfalls pending. Spätere Fehler setzen sie grundsätzlich ERRED, sofern nicht bereits DONE. (Quelle: `waldur_site_agent/common/processors.py:960-963,1090-1152` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Nur `UnexpectedStatus` und `httpx.TransportError` werden in einem Durchlauf bis zu zehnmal mit fünf Sekunden Pause wiederholt. (Quelle: `waldur_site_agent/common/processors.py:913-948` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Der generische Create-Pfad meldet vorhandene IDs als `DuplicateResourceError`; der Processor besitzt dafür einen Uniqueness-Retry-Pfad. (Quelle: `waldur_site_agent/backend/backends.py:878-883` und `waldur_site_agent/common/processors.py:629-638` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

## 6. DigitalOcean und Blaupause

DigitalOcean ist **nicht nur Sync**: Es erstellt echte Droplets aus Region, Image, Size, User-Data, Tags und SSH-Key und liefert die Droplet-ID. (Quelle: `plugins/digitalocean/waldur_site_agent_digitalocean/backend.py:178-245` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Es implementiert Delete, Shutdown für Downscale/Pause, Power-on für Restore und limitbasiertes Resize. (Quelle: `plugins/digitalocean/waldur_site_agent_digitalocean/backend.py:247-317` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Es ist dennoch keine vollständige Blaupause: Usage ist immer `{}`; Associations, User-Limits, Usage und Resource-User sind im Client No-op oder leer. (Quelle: `plugins/digitalocean/waldur_site_agent_digitalocean/backend.py:76-78` und `plugins/digitalocean/waldur_site_agent_digitalocean/client.py:125-174` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

Aktionsmethoden liefern IDs, doch das Backend verwirft sie und aktiviert Async-Orders nicht; explizites Polling ist dort **NICHT GEFUNDEN**. (Quelle: `plugins/digitalocean/waldur_site_agent_digitalocean/client.py:211-237`, `plugins/digitalocean/waldur_site_agent_digitalocean/backend.py:20-53,266-317` und `waldur_site_agent/backend/backends.py:46-50` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

**Primäre provider-taugliche Blaupause: OpenNebula.** Sie enthält reales Create/Delete, Limits, Standard-Usage und alle abstrakten Lifecycle-Hooks. (Quelle: `plugins/opennebula/waldur_site_agent_opennebula/backend.py:674-700,833-918,1385-1405` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

**Sekundäre Blaupause: DigitalOcean.** Sie passt für einfache Public-Cloud-VM-Attribute und Lifecycle; Usage, Membership und Async-Warten müssen ergänzt werden. (Quelle: `plugins/digitalocean/waldur_site_agent_digitalocean/backend.py:93-176,178-317` und `plugins/digitalocean/waldur_site_agent_digitalocean/client.py:125-174` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)

## 7. Provider-Abnahme

- Export unter `waldur_site_agent.backends`; optionale Schemas unter demselben Namen. (Quelle: `plugins/digitalocean/pyproject.toml:20-29` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- Alle zehn abstrakten Methoden aus Abschnitt 2.1 implementieren. (Quelle: `waldur_site_agent/backend/backends.py:135-325,491-514,826-848` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- Create liefert eine nichtleere `BackendResourceInfo.backend_id`; leer wird `BackendError`. (Quelle: `waldur_site_agent/common/processors.py:1182-1188` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- Nicht unterstützte Operationen verwenden dokumentierte No-op-Rückgaben. (Quelle: `waldur_site_agent/backend/backends.py:225-227,256-325,491-514` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- Providerfehler als `BackendError`, temporäre Nichtbereitschaft als `BackendNotReadyError` sichtbar machen. (Quelle: `waldur_site_agent/backend/exceptions.py:6-7,41-46` und `waldur_site_agent/common/processors.py:1090-1152` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
- Kollision, Wiederholung, Teilprovisionierung und Async-Zustand explizit testen; der generische Retry erfasst nur zwei HTTP-Fehlerklassen. (Quelle: `waldur_site_agent/backend/backends.py:850-883` und `waldur_site_agent/common/processors.py:913-948` @ `0cb51a188850aeccde9fdca94cfae41cb707b7b6`)
