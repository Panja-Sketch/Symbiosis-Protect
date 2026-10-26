# SOURCES

Every fact or dataset behind rules, seed data and UI copy. Provenance labels: HISTORIC (archives) · SYNTHETIC (invented demo data) · LIVE (Phase 2).

## Datasets (built by `scripts/`, outputs in `data/derived/`)
| Dataset | Used for | Link | Notes |
|---|---|---|---|
| Open-Meteo Historical Weather API, 1991–2025 | 5-yr heat/freeze/precip stats and 1991–2020 monthly normals per location | https://open-meteo.com/en/docs/historical-weather-api | ERA5-based reanalysis grid values, not station records; non-commercial tier only |
| NOAA NCEI Storm Events Database, 2016–2025 | Storm-event counts and damage by county/zone | https://www.ncei.noaa.gov/stormevents/ (bulk: https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/) | Public domain; recent years are provisional |
| FEMA National Risk Index v1.20 (Dec 2025), county + census tract | Expected-annual-loss ratings per hazard | https://hazards.fema.gov/nri/ | Scores are national percentiles; AZ-tract percentile computed by us |
| NWS API (points metadata, zones) | Zone/county/grid per location | https://www.weather.gov/documentation/services-web-api | Live forecast/alerts arrive in Phase 2 |
| FCC Census Block API | Census tract for each location | https://geo.fcc.gov/api/census/ | |
| Open-Meteo Elevation API | Elevation per location | https://open-meteo.com/en/docs/elevation-api | |

## Reference facts for rules and copy
| Fact | Source |
|---|---|
| NWS monsoon season is June 15 – September 30; Phoenix seasonal average about 2.43 in (1991–2020) | NWS Phoenix, as reported by Arizona Republic — https://www.weather.gov/psr/monsoon |
| Water heaters fail around 10.7 years on average (~75% by 12 years); washer supply hoses around 8.7 years | IBHS (Insurance Institute for Business & Home Safety) water-damage research — https://ibhs.org |
| Non-weather water claim severity up 63% (2019–2025) | LexisNexis Risk Solutions, Home Trends 2026 report — https://risk.lexisnexis.com |
| Phoenix-area water hardness around 12 grains/gal (assumption; configurable) | Water-treatment vendor pages; verify against the City of Phoenix Water Quality Report before production |
| Clogged AC condensate lines are a common cause of Arizona indoor water damage | Restoration-industry observation — label as industry observation, not a statistic |
| Open-Meteo archive covers 1940–present, free for non-commercial use | https://open-meteo.com/en/pricing |

## Synthetic data (labelled SYNTHETIC in the UI)
Personas, accounts, agencies, policies, assets, claims, task history and devices are invented. Coordinates are real city coordinates with a small deterministic jitter; street names are not used. Policy summaries are original plain-language text — no ISO or insurer wording is copied.
