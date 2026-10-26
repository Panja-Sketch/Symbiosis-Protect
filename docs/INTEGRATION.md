# INTEGRATION

Every external dependency sits behind an interface in `api/app/adapters/protocols.py`. OpenAPI for the HTTP surface is served at `/docs` (`/openapi.json`).

| Adapter | Contract | Demo implementation | What a real implementation needs |
|---|---|---|---|
| `PolicySource` | `get_policy(id)`, `list_policies(account_id)` → `Policy` (api/app/models.py) | JSON seed in `data/seed/policies.json`, loaded into the store | Carrier policy-admin API (auth, mapping of coverage codes/limits/endorsements to our `Coverage`/`Endorsement`, plain-language text maintained by the carrier or generated and reviewed), rate limits, change notifications |
| `WeatherProvider` | `forecast(loc)` → `Forecast`, `active_alerts(loc)` → `list[WeatherAlert]` | `CompositeWeatherProvider(NWSProvider, OpenMeteoProvider)` behind `ScenarioProvider` (Director injections, always `SIMULATED`) | NWS needs no key but requires `User-Agent` with contact (`NWS_USER_AGENT`); cache points 7 d, forecast 30 min, alerts 5 min (implemented). Open-Meteo commercial plan (or NOAA/NCEI) for production |
| `HistoryProvider` | `stats(loc)` → derived history JSON | `DerivedHistoryProvider` over `data/derived/*.json` (Open-Meteo archive, NCEI Storm Events, FEMA NRI) | BigQuery or a warehouse table keyed by location; NOAA NCEI instead of Open-Meteo for licensing |
| `Notifier` | `send(alert, account, now)` → channels | `InAppNotifier` (alert persisted), `ConsoleEmailNotifier` (logs + `outbox`; respects channel prefs and quiet hours, critical bypasses quiet hours) | SMTP/SES/SendGrid via Secret Manager; Twilio for SMS (consent, opt-out, 10DLC registration); delivery receipts |
| `DeviceAdapter` | `readings(device_id, since)`, `command(device_id, "shutoff"/"open")` | `SimulatedWaterDevice` (Phase 6) | Vendor API per device (Flo, Phyn, LeakBot, multifamily vendor): OAuth, webhook ingestion, unit mapping, command support flags |
| `AIExplainer` | `answer(question, ctx)`, `phrase_task(rule, ctx)` | `TemplateExplainer` fallback + Gemini (Phase 5) | Vertex AI service account, model name in `GEMINI_MODEL`, response schema validation |
| `Cache` | `get/set(key, ttl)` | `MemoryCache`, `FirestoreCache` (`cache` collection with `expires_at` TTL) | Enable a Firestore TTL policy on `cache.expires_at` in the cloud project |
| `Store` | `get/put/delete/list` | `MemoryStore` (tests), `FirestoreStore` (emulator/cloud) | Production Firestore with security rules (`infra/firestore.rules` denies all client access; the API uses the Admin SDK) |

## Playbooks (rules)
All thresholds are in YAML under `api/app/playbooks/` (`homeowners.yaml`, `bop.yaml`, `cre.yaml`, `agribusiness.yaml`, `thresholds.yaml`, `scoring.yaml`, `proof_policy.yaml`, `scenarios.yaml`). A rule is `applies_if` + `when` (`any`/`all` of named conditions) + `steps`. Conditions are implemented in `engine/conditions.py`; adding a rule needs no Python unless it needs a new condition type. The AI never decides tasks — rules do.
