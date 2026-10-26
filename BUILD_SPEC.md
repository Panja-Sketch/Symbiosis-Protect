# Symbiosis Protect — Arizona Demo · Build Specification v1

> Hand this file to Claude Code in an empty repo. Build **locally first**, then deploy to Google Cloud.
> Owner: Charan Panja · Date: 2026-10-25 · Scope: Arizona only · Status: LOCKED objectives (Section 1)

---

## 0. How to use this spec (instructions to Claude Code)

1. Read the whole file before writing code. Then read `CLAUDE.md` (standing rules).
2. Build in the phase order in Section 13. Do not start a phase until the previous phase's **Definition of Done** passes.
3. After each phase: run all checks, commit with a message `phase-N: <summary>`, and append a short entry to `docs/STATUS.md` (what works, what is stubbed, known gaps).
4. When something in this spec is impossible or ambiguous, choose the simplest option that keeps the **locked objectives** true, write the decision in `docs/DECISIONS.md`, and continue.
5. Never present simulated, synthetic or AI-generated data as live or real. Every data point on screen carries a provenance label (Section 7.4).

---

## 1. Locked end-to-end objectives

The demo is done when **all** of these are true, on a phone and on a laptop:

| # | Objective | Proof it works |
|---|---|---|
| O1 | A policyholder sees **what is insured** for their line of business, in plain language: coverages, limits, deductibles, endorsements, key exclusions | Policy screen for each of the 6 demo personas |
| O2 | The app gives **timely, specific, step-by-step actions** to prevent losses, driven by (a) live weather, (b) location history, (c) property and equipment age, (d) the policy's coverages | At least 3 tasks per persona, each with a "why this, why now" explanation citing its inputs |
| O3 | **Live** Arizona weather and **official NWS alerts** are used, plus **historic** weather and storm data for the location | Weather card shows LIVE badge; history panel shows 5-year stats; alert rules fire on real NWS alerts when present |
| O4 | **Alerts** reach the user in-app (and by email in console/dev mode), with one-tap actions | Notification center + Scenario Director can force any alert type |
| O5 | The user can **ask the AI** about their coverage and benefits; answers are grounded only in their policy data and cite which coverage they come from; anything advisory hands off to the agent | Assistant panel; refuses to invent coverage; shows sources |
| O6 | The user can **mark tasks done with proof** (one-tap or in-app photo with time and location) — proof levels configurable | Task completion flow; Evidence tab |
| O7 | **Sense mode**: connect a (simulated) water device; a leak opens a case → alert → action → **sensor-verified** fix → case closed → reopens if it recurs | Sense demo for Homeowners and Commercial Real Estate personas |
| O8 | **Agent** and **Underwriter** views show the same records from their side | Role switcher; agent book view; underwriter participation + evidence |
| O9 | **Integration-ready**: every external dependency sits behind an adapter interface with a demo implementation and an OpenAPI-documented contract | `docs/INTEGRATION.md` + adapter folders + `/docs` OpenAPI |
| O10 | Runs locally with one command, deploys to Cloud Run within the $200 GCP budget | `make dev` / `make deploy`; budget alerts configured |

**Out of scope for v1:** real authentication for customers, real payments, real SMS, real device vendors, states other than Arizona, premium discounts/rating.

---

## 2. Positioning (so UI copy and AI answers stay consistent)

- **Two modes on one customer record** — the property equivalent of how Progressive Snapshot and State Farm Drive Safe & Save are both opt-in programs layered on an existing policy:
  - **Guide mode (no device):** alerts, guidance, step-by-step actions from policy + property + history + public data + live weather.
  - **Sense mode (opt-in device):** leak/flow/temperature device, closed loop with sensor verification.
- Carrier branding is **configurable** (`CARRIER_NAME`, `CARRIER_PRIMARY_COLOR`, logo slot). Default display name: **"Symbiosis Protect"**. Do **not** ship any real insurer logo.
- **Primary peril: water.** Secondary: heat/monsoon/freeze conditions that cause water and property losses.
- **Honest note for the demo script:** public sources indicate the target carrier writes **commercial and agricultural** lines in Arizona and **personal** lines only in CA/NV/OR/WA. The Homeowners and Dwelling Fire personas are therefore labelled **"Personal-lines preview (AZ demo data)"** in the UI. The Arizona commercial/ag personas are the primary story.

---

## 3. Tech stack (mirrors RateGuard so you can reuse patterns)

| Layer | Choice | Notes |
|---|---|---|
| Frontend | **Next.js 14 (App Router) + TypeScript + Tailwind CSS** | Same as RateGuard |
| UI kit | **shadcn/ui (Radix primitives)**, **lucide-react** icons, **Framer Motion** (subtle), **Recharts** (charts), **MapLibre GL** + free OSM-style tiles *or* a static SVG Arizona map (pick static SVG if tiles add cost/complexity) | No paid UI kits |
| Backend | **Python 3.12 + FastAPI + Pydantic v2** | Same as RateGuard |
| AI | **Vertex AI Gemini (Flash-Lite class)** via `google-genai` SDK, service-account auth (no API key in code). Model name in config: `GEMINI_MODEL` | Fallback: deterministic templated answer when AI is unavailable |
| Data store | **Firestore** (emulator locally) | Collections in Section 6 |
| Files | Local disk in dev; **Cloud Storage** in cloud (proof photos, evidence ZIPs) | Signed URLs |
| Jobs | Local: APScheduler in the API process. Cloud: **Cloud Scheduler → authenticated POST /internal/evaluate** every 15 min | No Pub/Sub needed in v1 |
| Auth (demo) | **Demo persona switcher** with signed session cookie (HMAC). Firebase Auth behind a feature flag `AUTH_MODE=firebase` for later | Clearly labelled "Demo identity" |
| Tests | pytest + ruff (API); Jest/Vitest + Playwright incl. mobile viewport + axe a11y (web) | |
| Deploy | Docker → Artifact Registry → **Cloud Run** (`web`, `api`), Cloud Build or `gcloud run deploy --source` | Scale to zero |
| Package mgmt | `uv` or `pip` for API; `pnpm` for web | Single `Makefile` at root |

---

## 4. Demo personas (all synthetic, Arizona)

Use **real city coordinates** (slightly jittered) with **fictional** street names. Never use a real person's address.

| ID | Persona | LOB / product | Location | Why it demos well |
|---|---|---|---|---|
| P1 | **Maya, new homeowner** | Homeowners (HO-3 style) — *personal-lines preview* | Chandler (33.3062, -111.8413) | 1998 home, original water heater unknown age, washer hoses rubber; monsoon + extreme heat AC condensate risk; hard water |
| P2 | **Luis, landlord** | Dwelling Fire (rental) — *personal-lines preview* | Tucson (32.2226, -110.9747) | Tenant turnover, vacancy, water heater 11 yrs, slow-leak risk unseen by owner |
| P3 | **Saguaro Grill (restaurant)** | Businessowners (BOP) | Tempe (33.4255, -111.9400) | Ice-maker/dishwasher lines, AC condensate over dining room, monsoon roof drains, slip-and-fall after water |
| P4 | **Ponderosa Outfitters (retail)** | Businessowners (BOP) | Flagstaff (35.1983, -111.6513) | **Freeze** demo: hard freezes, holiday closure, wet sprinkler, snow load |
| P5 | **Mesa Palms Apartments (48 units)** | Commercial Real Estate (habitational) | Mesa (33.4152, -111.8315) | Unit-to-unit water cascades, unit register, Sense mode with unit sensors |
| P6 | **Desert Bloom Produce (cooler + packing)** | Commercial Agriculture / AgriBusiness | Yuma (32.6927, -114.6277) | Refrigeration + wash-down water, extreme heat, power, pre-harvest checklist; reuses the original Symbiosis cold-storage idea |

Each persona gets: a policy JSON (Section 6), a property/asset profile, 0–2 prior claims (synthetic), an assigned **agent** (synthetic independent agency), and a seeded task history.

---

## 5. Arizona risk model (what drives recommendations)

All thresholds live in versioned YAML (`api/app/playbooks/*.yaml`), never hard-coded in Python.

### 5.1 Hazards and triggers

| Hazard | Arizona context | Live trigger (examples) | Historic signal |
|---|---|---|---|
| **Monsoon storms** | NWS official season **June 15 – Sept 30** (Phoenix avg ~2.43" in season, 1991–2020) | NWS Severe Thunderstorm Watch/Warning, Flash Flood Watch/Warning, Dust Storm Warning in the location's zone; forecast precip ≥ 0.5"/24h | Count of monsoon-season storm events in county, last 10 yrs (NCEI) |
| **Extreme heat** | Long stretches ≥ 110°F in low deserts | NWS Extreme Heat Warning / Excessive Heat Warning; forecast max ≥ 110°F for ≥ 2 days | Days ≥ 110°F per year, last 5 yrs (Open-Meteo archive) |
| **AC condensate overflow** (water) | Heavy AC runtime; clogged condensate lines are a leading cause of AZ indoor water damage (restoration-industry sources) | Heat trigger above **and** last condensate-line service > 6 months (or unknown) | — |
| **Freeze** | High country (Flagstaff, Prescott, Show Low) hard freezes; occasional low-desert freeze | NWS Hard Freeze / Freeze Warning, Extreme Cold Warning; forecast min ≤ 28°F (high country) or ≤ 32°F (desert) within 72 h | Nights ≤ 28°F per winter, last 5 yrs |
| **Hard water / appliance age** | Phoenix-area water ~12 grains/gal (very hard) — shortens water-heater and hose life (vendor estimates; treat as an *assumption*, configurable) | Water heater age ≥ **8 yrs** in hard-water zones (≥ 9 elsewhere); washer/ice-maker hoses ≥ **5 yrs** or rubber | IBHS: heaters fail ~10.7 yrs avg nationally; washer hoses ~8.7 yrs |
| **Flash flood / surface water** | Monsoon flash floods; standard policies exclude flood | NWS Flash Flood Warning | FEMA NRI riverine flood EAL for the tract/county |
| **Hail / wind** | Monsoon microbursts and hail | Severe Thunderstorm Warning with hail/wind tags | NCEI hail/wind events in county |

### 5.2 Recommendation playbook format

```yaml
id: az.ho.condensate.heat.v1
lob: [homeowners, dwelling_fire, bop, commercial_real_estate]
peril: water
title: "Flush your AC condensate line before the heat wave"
why_template: >
  {city} is forecast to hit {max_temp_f}°F for {days} days. Your AC will run
  almost nonstop, and a clogged condensate line is one of the most common causes of
  indoor water damage in Arizona. Your last service on file: {last_service|unknown}.
applies_if:
  has_central_ac: true
when:
  any:
    - nws_event: ["Extreme Heat Warning", "Excessive Heat Warning"]
    - forecast_max_temp_f: { gte: 110, min_days: 2, within_hours: 96 }
  and:
    - asset_last_service_months: { asset: hvac_condensate, gte: 6, or_unknown: true }
steps:
  - "Find the condensate line (PVC pipe near the indoor air handler)."
  - "Pour 1 cup of distilled vinegar into the access port; wait 30 minutes."
  - "Check the outside drain end is dripping, not dry."
  - "If the drain pan has water standing, call an HVAC technician."
est_minutes: 20
est_cost_usd: [0, 150]
proof: { default_level: E1, accepted: [E0, E1, E2] }
coverage_note_key: water_sudden_vs_gradual
priority: high
expires_after_hours: 96
cooldown_days: 30
sources: [ "NWS alert or forecast", "asset profile" ]
```

**Minimum playbook set for v1 (≈ 24 rules):**
- Homeowners/Dwelling (8): condensate+heat, water heater age, washer/ice-maker hose age, monsoon roof & gutters/scuppers, flash-flood readiness + flood-coverage gap note, travel/vacancy shutoff, freeze (high country only), know-your-shutoff onboarding.
- BOP (6): holiday closure shutoff+heat (Flagstaff), freeze sprinkler 40°F rule, ice-maker/dishwasher lines (restaurant), condensate+heat, monsoon roof drains + rooftop units secured, wet-floor/slip response after water event.
- Commercial Real Estate (6): unit register onboarding, unit-turnover supply-line check, water-heater age by unit, riser/roof drains pre-monsoon, heat + condensate in units, leak in upper unit → notify units below.
- AgriBusiness (4): pre-harvest refrigeration service, extreme-heat power/backup check, wash-down hose & backflow check, monsoon power-outage/spoilage plan.

### 5.3 Prioritization (deterministic)

`score = severity_weight(peril, lob) × urgency(time_to_event) × exposure(asset_age, prior_claims, NRI_EAL_percentile) × (1 − completion_recency)`
Show **max 3 open "Do now" tasks** per persona; the rest go to "Coming up". Insurer-issued items (from the underwriter view) are never hidden by the cap.

---

## 6. Data model (canonical contracts)

Field names follow common insurance terminology (ACORD-like spirit) but are our own. Store as Firestore documents; expose via OpenAPI.

```text
Account        { id, persona_id, display_name, type: person|business, agent_id, contact{email,phone}, preferences{channels,quiet_hours} }
Location       { id, account_id, label, city, county, lat, lon, nws_zone, nws_county, fema_tract_id, elevation_ft, hard_water_zone: bool }
Policy         { id, account_id, lob: homeowners|dwelling_fire|bop|commercial_real_estate|agribusiness,
                 product_label, term{start,end}, status, coverages[Coverage], endorsements[Endorsement],
                 exclusions_plain[ExclusionNote], deductibles{all_peril, water?}, preview_flag: bool }
Coverage       { code, name_plain, limit_usd, deductible_usd?, what_it_covers_plain, what_it_does_not_plain, examples[] }
Endorsement    { code, name_plain, present: bool, why_it_matters_plain }
Asset          { id, location_id, type: water_heater|washer_hoses|ice_maker_line|hvac_condensate|roof|sprinkler_system|refrigeration|unit, 
                 install_year?, last_service_date?, material?, unit_label?, notes }
Claim          { id, policy_id, date, peril, cause, paid_usd (synthetic) }
Task           { id, rule_id, policy_id, location_id, asset_id?, source: rule|insurer|agent, title, why, steps[], priority,
                 status: open|done|deferred|declined|expired, due_at, opened_at, closed_at,
                 inputs_snapshot{weather, alert_ids, asset_ages, coverage_keys}, proof[Proof], visibility: private|shared }
Proof          { id, level: E0|E1|E2|E3|E4, type: attest|photo|document|review|sensor, captured_at, lat?, lon?, sha256, uri?, by_user }
Alert          { id, account_id, kind: weather|task|device|agent, severity, title, body, deep_link, sent_channels[], read_at }
Device         { id, location_id, vendor: simulated|flo|phyn|leakbot|generic, model, status, last_seen }
Reading        { device_id, ts, metric: flow_lpm|leak|temp_f|humidity, value, quality }
Case (Sense)   { id, device_id, task_id, state: detected|alerted|acting|verifying|verified|not_improving|inconclusive|reopened, timeline[] }
EvidencePackage{ id, policy_id, scope, files[], manifest_sha256, created_at, shared_with[] }
Agent          { id, agency_name (synthetic), name, email }
```

Seed files live in `data/seed/` (JSON) and load with `make seed`.

---

## 7. External data & adapters

### 7.1 Live weather and alerts
- **NWS API** `https://api.weather.gov` — free, no key; **must send a `User-Agent` header** with app name + contact email (env `NWS_USER_AGENT`).
  - Point metadata: `/points/{lat},{lon}` → forecast URLs, zone, county.
  - Hourly forecast: `/gridpoints/{office}/{x},{y}/forecast/hourly`.
  - Active alerts: `/alerts/active?point={lat},{lon}`.
  - Cache: points 7 days; forecast 30 min; alerts 5 min (Firestore cache collection with TTL).
- **Open-Meteo forecast** `https://api.open-meteo.com/v1/forecast` — backup/secondary source for daily max/min.

### 7.2 Historic data
- **Open-Meteo Historical** `https://archive-api.open-meteo.com/v1/archive` — daily max/min temp + precipitation for the last 5 years per persona location. Pre-compute stats with `scripts/build_history.py` → `data/derived/history_{location_id}.json` (days ≥110°F, nights ≤28°F, wettest day, monsoon-season totals). **License: free tier is non-commercial — fine for the demo; a production deployment needs Open-Meteo's commercial plan or NOAA/NCEI data instead.** Record this in `docs/DECISIONS.md`.
- **NOAA NCEI Storm Events Database** (bulk CSV, public) — filter `STATE == ARIZONA`, last 10 years, counties of the 6 personas; keep event type, date, county, damage fields. Script: `scripts/build_storm_events.py` → `data/derived/storm_events_az.json`.
- **FEMA National Risk Index** (CSV, public, county and census tract) — extract Arizona rows, keep expected-annual-loss scores for heat wave, riverine flooding, hail, strong wind, cold wave, winter weather. Script: `scripts/build_nri.py` → `data/derived/nri_az.json`.
- Scripts must be **idempotent**, cache raw downloads in `data/raw/` (git-ignored), and commit only the small derived JSON.

### 7.3 Adapter interfaces (integration-ready)

```python
class PolicySource(Protocol):      # demo: JSON seed  → later: carrier policy admin API
    def get_policy(self, policy_id: str) -> Policy: ...
    def list_policies(self, account_id: str) -> list[Policy]: ...

class WeatherProvider(Protocol):    # NWSProvider, OpenMeteoProvider, ScenarioProvider (demo injection)
    def forecast(self, loc: Location) -> Forecast: ...
    def active_alerts(self, loc: Location) -> list[WeatherAlert]: ...

class HistoryProvider(Protocol):    # derived JSON now → BigQuery later
    def stats(self, loc: Location) -> HistoryStats: ...

class Notifier(Protocol):           # InAppNotifier, ConsoleEmailNotifier (dev), SMTPNotifier/Twilio later
    def send(self, alert: Alert) -> DeliveryResult: ...

class DeviceAdapter(Protocol):      # SimulatedWaterDevice now → Flo/Phyn/LeakBot/generic webhook later
    def readings(self, device_id: str, since: datetime) -> list[Reading]: ...
    def command(self, device_id: str, action: Literal["shutoff","open"]) -> CommandResult: ...

class AIExplainer(Protocol):        # GeminiExplainer, TemplateExplainer (fallback)
    def answer(self, question: str, ctx: PolicyContext) -> GroundedAnswer: ...
    def phrase_task(self, rule: Rule, ctx: TaskContext) -> str: ...
```

`docs/INTEGRATION.md` must describe, for each adapter: contract, demo implementation, and what a real carrier/vendor implementation needs (auth, data mapping, rate limits).

### 7.4 Provenance labels (mandatory on every data element in UI)
`LIVE` (NWS/Open-Meteo now) · `HISTORIC` (archive/NCEI/NRI) · `SYNTHETIC` (seeded policy/claims/devices) · `SIMULATED` (Scenario Director or simulated device) · `AI` (generated wording). Small pill badge, tooltip explains source + timestamp.

---

## 8. AI assistant ("Ask about my coverage")

- **Grounding:** the model receives only: the persona's `Policy` (coverages, endorsements, exclusions_plain, deductibles), open tasks, and a curated glossary (`data/seed/glossary.json`). No web access.
- **Output schema (enforced):** `{ answer_plain, cited_coverage_codes[], confidence: high|medium|low, needs_agent: bool, suggested_actions[] }`. Validate; if invalid or AI unavailable → TemplateExplainer.
- **Rules (system prompt + post-validation):**
  1. Answer only from the provided policy data; if not present → say so and set `needs_agent=true`.
  2. Never state that a specific loss **will** be covered; use "your policy summary says…" and "your agent confirms final coverage decisions".
  3. No legal, pricing, or claims-decision advice. Endorsement suggestions are phrased as "ask your agent about…".
  4. Every claim in the answer maps to a `cited_coverage_codes` entry; UI shows those as chips that open the coverage card.
- **Starter questions per LOB** (chips), e.g. "Is water from my AC covered?", "What does my water-backup endorsement do?", "Am I covered for monsoon flooding?", "What if a tenant's leak damages the unit below?", "Does my policy cover spoiled produce if the cooler fails?"
- **Coverage text:** write **original plain-language summaries** in seed data. Do **not** copy ISO or any insurer's policy wording.
- Log every AI call (prompt hash, model, latency, fallback used) to Firestore `ai_logs`.

---

## 9. UX & visual design

### 9.1 Design direction — "Desert Instrument"
Calm, precise, enterprise; unique through an Arizona-dusk palette and one signature element.

- **Palette (tokens in `globals.css`, light + dark):** ink `#0F1B2D`, slate surfaces, **accent "Monsoon Teal"** `#0E9F9A`, **warm "Mesa Clay"** `#C2603A` for warnings, **"Saguaro"** `#2F7D4F` for done/verified, **"Haboob Amber"** `#D9A441` for watch-level. Check contrast ≥ 4.5:1 for text; generate dark-mode equivalents.
- **Type:** Inter (UI) + a characterful display face for headings (e.g., "Fraunces" or "Space Grotesk") from Google Fonts. Numbers tabular.
- **Shape:** 12px radius cards, 1px hairline borders, soft elevation only on interactive surfaces.
- **Motion:** 150–250 ms; respect `prefers-reduced-motion`.
- **Signature element: the 7-day "Risk Ribbon"** — a horizontal strip at the top of Home showing each of the next 7 days as a tile (icon + temp + risk color), with task pins dropped on the day they matter. Tap a day → what to do that day. On phone it scrolls horizontally with snap.
- **Second signature: "Coverage Lens"** — tapping any task shows a side sheet: *What could happen · What your policy says (with coverage chip) · What to do · Proof*.

### 9.2 Layout
- **Phone (< 768px):** bottom tab bar (Home · Tasks · Coverage · Ask · More), sheets instead of modals, sticky primary action button, 44px touch targets.
- **Laptop (≥ 1024px):** left sidebar nav, 12-column grid, Home shows Risk Ribbon + Do-now tasks + Weather/Alerts + Local history side by side.
- **Role switcher** (top-right avatar): Policyholder ↔ Agent ↔ Underwriter; **persona switcher** for demos.

### 9.3 Screens (policyholder)
1. **Home** — greeting, Risk Ribbon, "Do now" (≤3), live weather + active NWS alerts, readiness ring (tasks done / applicable), local history teaser.
2. **Tasks** — tabs: Do now · Coming up · Done; task detail with numbered steps, est. time/cost, why-now inputs, proof capture.
3. **Coverage** — "What's insured" cards per coverage (limit, deductible, covers / doesn't cover, examples), endorsements present/missing, exclusions in plain words, agent contact.
4. **Ask** — chat with starter chips, cited coverage chips, "Talk to my agent" handoff.
5. **My place** — assets with ages (water heater, hoses, AC, roof…), editable; local history charts (heat days, freeze nights, storm events, NRI percentiles).
6. **Alerts** — notification center with filters.
7. **Sense** — connect device (simulated), live tiles (flow, leak, temp), case timeline.
8. **Settings** — channels, quiet hours, data sharing (what the insurer sees; per-task share toggle).

### 9.4 Agent view
Book of clients (6 personas) with: open high-priority tasks, last activity, Sense status, upcoming weather exposure (which clients are under an active alert), suggested renewal talking points (AI-phrased, labelled).

### 9.5 Underwriter / risk-control view
Portfolio tiles: participation, task completion %, proof-level mix (E0–E4), active alerts by county, Sense cases; account drill-down with evidence package export (ZIP + SHA-256 manifest). **Shows only shared/insurer-issued items** per privacy rules; can **issue a recommendation** that appears as an insurer-issued task.

### 9.6 Accessibility & quality bar
WCAG 2.2 AA, keyboard navigable, focus rings, aria labels, axe checks in Playwright, Lighthouse mobile ≥ 90 performance / ≥ 95 accessibility on Home.

---

## 10. Sense mode (closed loop)

- **SimulatedWaterDevice** emits readings every 5 s in demo (flow L/min, leak bool, temp °F) with scenarios: normal, slow leak, burst, freeze-risk temp drop, recovery.
- **State machine:** `detected → alerted → acting → verifying → verified | not_improving | inconclusive → (reopened if recurrence within watch window)`. Verification is **deterministic**: e.g., leak sensor dry and flow back to baseline for N consecutive readings after the user reports the fix. Missing/stale data → `inconclusive`, never `verified`.
- **Shutoff command** (simulated) available when vendor supports it.
- Commercial Real Estate: leak in Unit 3B auto-creates a "check unit below (2B)" task.
- Evidence package for a closed case includes readings window, actions, timestamps, hashes.

---

## 11. Scenario Director (demo control panel)

Hidden route `/director` (also a floating button in demo mode) to **inject** events so the demo works on a calm-weather day. Everything injected is labelled `SIMULATED`.

Buttons: *Freeze Warning – Flagstaff* · *Excessive/Extreme Heat Warning – Phoenix metro* · *Severe Thunderstorm + Flash Flood Warning – Tempe/Mesa* · *Dust Storm Warning – I-10* · *Slow leak – Mesa Palms Unit 3B* · *Burst – Maya's laundry* · *Cooler temperature drift – Desert Bloom* · *Reset demo*.
Also: time-travel slider ("pretend it's July 18") so seasonal rules (monsoon) can be shown in October.

---

## 12. API surface (FastAPI, `/api/v1`)

```
GET  /personas                          GET  /accounts/{id}
GET  /accounts/{id}/policies            GET  /policies/{id}
GET  /locations/{id}/weather            GET  /locations/{id}/alerts
GET  /locations/{id}/history            GET  /locations/{id}/risk-ribbon
GET  /accounts/{id}/tasks?status=       POST /tasks/{id}/complete   (multipart proof)
POST /tasks/{id}/defer | /decline       POST /tasks (insurer-issued; underwriter role)
POST /assistant/ask                     GET  /alerts?account_id=   POST /alerts/{id}/read
GET  /devices?location_id=              POST /devices/connect      GET /devices/{id}/readings
GET  /cases/{id}                        POST /cases/{id}/report-fix
GET  /agent/book                        GET  /underwriting/portfolio
POST /evidence/{policy_id}/export
POST /internal/evaluate                 (scheduler; OIDC-protected in cloud)
POST /director/inject  /director/reset  /director/time-travel   (demo mode only)
GET  /healthz
```
OpenAPI at `/docs`. All responses include `provenance` where relevant.

---

## 13. Build phases & Definition of Done

| Phase | Build | Definition of Done |
|---|---|---|
| **0 Scaffold** | Monorepo: `web/`, `api/`, `data/`, `scripts/`, `infra/`, `docs/`; Makefile (`dev`, `seed`, `test`, `lint`, `deploy`); Firestore emulator; env templates (`.env.example` names only) | `make dev` starts web + api + emulator; health check green |
| **1 Data** | `build_history.py`, `build_storm_events.py`, `build_nri.py`; seed 6 personas, policies, assets, claims, agents, glossary | Derived JSON committed; `make seed` loads; unit tests on parsers |
| **2 Engine** | Weather adapters (NWS + Open-Meteo + Scenario), cache, playbook loader, rule evaluator, prioritizer, task lifecycle, alert creation, scheduler | Given fixtures, rules produce expected tasks (golden tests); real NWS call works with User-Agent |
| **3 UI core** | Design tokens, layout shells (phone/laptop), Home + Risk Ribbon, Tasks, Coverage, My place, Alerts; provenance pills | Playwright passes at 390×844 and 1440×900; axe clean |
| **4 Proof** | Task complete with E0/E1 (camera capture, timestamp, geolocation if permitted, SHA-256), Evidence tab | Proof stored, hash shown, re-download works |
| **5 AI** | Assistant with grounding, schema validation, citations, fallback, logging | 20 scripted Q&A tests: no uncited claims, refuses unknowns |
| **6 Sense** | Simulated device, case state machine, verification, shutoff, reopen | Scenario: leak → verified → recurrence reopens |
| **7 Roles** | Agent book, Underwriter portfolio, insurer-issued task, evidence export, sharing rules | Role switch shows consistent data; private items hidden from underwriter |
| **8 Director** | Scenario Director, time-travel, reset | Full demo script (Section 15) runs end-to-end in < 8 min |
| **9 Deploy** | Dockerfiles, Cloud Run (`web`, `api`), Firestore native mode, GCS bucket, Cloud Scheduler, service accounts least-privilege, Vertex AI access, budget alerts | Public demo URL works on phone; costs within budget guardrails |

---

## 14. Google Cloud deployment & budget guardrails ($200 credit)

- Region: `us-central1` (or `us-west1`). Cloud Run **min instances 0**, max 2 per service, 512 MiB–1 GiB.
- Firestore native mode; GCS single bucket with lifecycle delete after 30 days for demo proof photos.
- Cloud Scheduler: 1 job, every 15 min (pause it when not demoing: `make scheduler-pause`).
- Gemini: Flash-Lite class model, max output tokens ~500, per-session rate limit (e.g., 30 asks/hour), response cache by (policy_id, normalized question).
- **Budget alerts** at $25 / $50 / $100 / $150 on the project; document how to tear down (`make destroy`).
- No BigQuery, Pub/Sub, or always-on instances in v1.
- Secrets: none required for NWS/Open-Meteo; any SMTP creds later via Secret Manager.

---

## 15. Demo script (target 7 minutes)

1. **Laptop, Maya (P1, Chandler):** Home → Risk Ribbon shows heat days → "Flush AC condensate line" task with why-now (LIVE forecast + unknown service date) → Coverage Lens: "sudden overflow vs gradual leak" plain-language note. *(1 min)*
2. **Ask:** "Is water from my AC covered?" → grounded answer with coverage chips + "confirm with your agent". *(45 s)*
3. **Phone, same user:** complete task with photo proof (E1) → readiness ring updates. *(45 s)*
4. **Director → Severe Thunderstorm + Flash Flood Warning (Tempe):** Saguaro Grill (P3) gets roof-drain + wet-floor tasks; flood-exclusion note. *(1 min)*
5. **Director → Freeze Warning (Flagstaff):** Ponderosa Outfitters (P4) holiday-closure + sprinkler 40°F steps. *(45 s)*
6. **Sense, Mesa Palms (P5):** slow leak Unit 3B → alert → "check 2B" task → report fix → **verified** by readings → recurrence reopens. *(1.5 min)*
7. **Agent view:** which clients are under active alerts; renewal talking points. **Underwriter view:** participation, proof mix, export evidence ZIP. *(1 min)*

---

## 16. Open questions (owner decides later — keep configurable)

- Which proof level closes advisory vs critical items (E1 vs E2)? → `config/proof_policy.yaml`.
- What share of insurer recommendations close with documentary proof today, and how is closure verified? (Ask risk control.)
- Should the underwriter ever see items the customer declined? Default **no** (private), configurable per tenant.
- Incentives (premium credit vs non-premium benefit) — UI placeholder only; no pricing logic in v1.
- Real device vendor for Sense pilot (Flo / Phyn / LeakBot / multifamily vendor).

---

## 17. Reference facts used in rules/copy (cite in `docs/SOURCES.md`)

- NWS monsoon season June 15 – Sept 30; Phoenix seasonal average 2.43" (1991–2020) — NWS via Arizona Republic.
- IBHS: water heaters fail ~10.7 yrs avg, ~75% by 12 yrs; washer supply hoses fail ~8.7 yrs avg; top water-loss sources = supply lines, toilets, water heaters, drains, washing machines.
- Non-weather water claim severity +63% (2019–2025) — LexisNexis Home Trends 2026.
- Phoenix water hardness ~12.3 grains/gal — water-treatment vendor pages (assumption; verify with city water quality report before production).
- NWS API is free, requires User-Agent; Open-Meteo archive covers 1940–present, free for non-commercial use.
- Clogged AC condensate lines are a leading cause of AZ indoor water damage — restoration-industry sources (label as industry observation).
