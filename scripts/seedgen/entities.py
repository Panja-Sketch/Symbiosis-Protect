"""Accounts, agents, assets, profiles, claims, task history, devices (all SYNTHETIC / SIMULATED)."""

import random
from datetime import date, datetime, timedelta

AGENTS = [
    {"id": "agent-1", "agency_name": "Sonoran Shield Insurance Group (synthetic)", "name": "Dana Whitfield",
     "email": "dana@sonoran-shield.example", "phone": "602-555-0142"},
    {"id": "agent-2", "agency_name": "Old Pueblo Risk Partners (synthetic)", "name": "Marcus Ybarra",
     "email": "marcus@oldpueblo-risk.example", "phone": "520-555-0177"},
    {"id": "agent-3", "agency_name": "High Country Agency (synthetic)", "name": "Priya Nakamura",
     "email": "priya@highcountry-agency.example", "phone": "928-555-0108"},
    {"id": "agent-4", "agency_name": "Colorado River Ag Insurance (synthetic)", "name": "Tomás Reyes",
     "email": "tomas@crag-insurance.example", "phone": "928-555-0163"},
]

ACCOUNTS = [
    {"id": "acct-p1", "persona_id": "P1", "display_name": "Maya Okafor", "type": "person",
     "headline": "New homeowner · Chandler", "agent_id": "agent-1",
     "contact": {"email": "maya@demo.example", "phone": "480-555-0111"},
     "program_label": "Personal-lines preview (AZ demo data)"},
    {"id": "acct-p2", "persona_id": "P2", "display_name": "Luis Mendoza", "type": "person",
     "headline": "Landlord · Tucson rental", "agent_id": "agent-2",
     "contact": {"email": "luis@demo.example", "phone": "520-555-0122"},
     "program_label": "Personal-lines preview (AZ demo data)"},
    {"id": "acct-p3", "persona_id": "P3", "display_name": "Saguaro Grill", "type": "business",
     "headline": "Restaurant · Tempe", "agent_id": "agent-1",
     "contact": {"email": "owner@saguaro-grill.example", "phone": "480-555-0133"}},
    {"id": "acct-p4", "persona_id": "P4", "display_name": "Ponderosa Outfitters", "type": "business",
     "headline": "Outdoor retail · Flagstaff", "agent_id": "agent-3",
     "contact": {"email": "manager@ponderosa-outfitters.example", "phone": "928-555-0144"}},
    {"id": "acct-p5", "persona_id": "P5", "display_name": "Mesa Palms Apartments", "type": "business",
     "headline": "48-unit apartment community · Mesa", "agent_id": "agent-1",
     "contact": {"email": "manager@mesa-palms.example", "phone": "480-555-0155"}},
    {"id": "acct-p6", "persona_id": "P6", "display_name": "Desert Bloom Produce", "type": "business",
     "headline": "Cooler & packing · Yuma", "agent_id": "agent-4",
     "contact": {"email": "ops@desert-bloom-produce.example", "phone": "928-555-0166"}},
]

TODAY = date(2026, 10, 25)


def _a(id, loc, type, label, **kw):
    return {"id": id, "location_id": loc, "type": type, "label": label, **kw}


def profiles():
    return [
        {"location_id": "loc-p1", "year_built": 1998, "sqft": 2150, "construction": "stucco frame",
         "roof_type": "concrete tile", "stories": 1, "has_central_ac": True, "occupancy": "owner_occupied",
         "notes": "Bought 2026. Seller records do not show water heater age or hose replacement."},
        {"location_id": "loc-p2", "year_built": 1984, "sqft": 1380, "construction": "block and stucco",
         "roof_type": "tile", "stories": 1, "has_central_ac": True, "occupancy": "vacant_between_tenants",
         "notes": "Lease ended 2026-10-18; next tenant expected 2026-12-01 (about 6 weeks vacant)."},
        {"location_id": "loc-p3", "year_built": 2006, "sqft": 5200, "construction": "masonry",
         "roof_type": "flat membrane with roof drains and scuppers", "stories": 1, "has_central_ac": True,
         "occupancy": "commercial_open", "notes": "Four rooftop AC units over the dining room and kitchen."},
        {"location_id": "loc-p4", "year_built": 1996, "sqft": 8400, "construction": "wood frame",
         "roof_type": "membrane, snow-load rated", "stories": 1, "has_central_ac": False,
         "occupancy": "commercial_open", "freeze_exposed_plumbing": True, "sprinkler_type": "wet",
         "scheduled_closures": [
             {"label": "Thanksgiving Day", "start": "2026-11-26", "end": "2026-11-26"},
             {"label": "Christmas closure", "start": "2026-12-24", "end": "2026-12-26"},
             {"label": "New Year's Day", "start": "2027-01-01", "end": "2027-01-01"}],
         "notes": "Back stockroom and sprinkler riser sit on an exterior wall."},
        {"location_id": "loc-p5", "year_built": 1988, "sqft": 41000, "construction": "wood frame, stucco",
         "roof_type": "flat roof with internal drains", "stories": 4, "has_central_ac": True,
         "occupancy": "multi_unit_residential", "unit_count": 48,
         "notes": "4 floors x 12 units (A-L). Unit label = floor number + letter, e.g. 3B sits above 2B."},
        {"location_id": "loc-p6", "year_built": 2009, "sqft": 22000, "construction": "insulated metal panel",
         "roof_type": "metal", "stories": 1, "has_central_ac": False, "occupancy": "agricultural_facility",
         "notes": "Two cooler rooms, packing line with wash-down, standby generator."},
    ]


def assets(rng_seed=48):
    out = [
        # P1 Maya — water heater age unknown on purpose
        _a("ast-p1-wh", "loc-p1", "water_heater", "Water heater (garage, 50 gal)", install_year=None,
           notes="Age unknown. Look for the serial number on the label; the first letter and two digits "
                 "often encode the manufacture month and year (varies by brand)."),
        _a("ast-p1-hoses", "loc-p1", "washer_hoses", "Washing machine hoses", material="rubber", install_year=None,
           notes="Rubber hoses, original to the home as far as the seller knew."),
        _a("ast-p1-ac", "loc-p1", "hvac_condensate", "AC condensate line (attic air handler)", last_service_date=None,
           notes="No service record from the seller."),
        _a("ast-p1-roof", "loc-p1", "roof", "Concrete tile roof", install_year=2009),
        _a("ast-p1-shutoff", "loc-p1", "main_shutoff", "Main water shutoff", notes="Location not yet confirmed by owner.", attributes={"location_confirmed": False}),
        # P2 Luis
        _a("ast-p2-wh", "loc-p2", "water_heater", "Water heater (hall closet, 40 gal)", install_year=2015),
        _a("ast-p2-ac", "loc-p2", "hvac_condensate", "AC condensate line", last_service_date=date(2025, 3, 14)),
        _a("ast-p2-roof", "loc-p2", "roof", "Tile roof", install_year=2012),
        _a("ast-p2-shutoff", "loc-p2", "main_shutoff", "Main water shutoff", notes="Front yard meter box, quarter-turn valve.", attributes={"location_confirmed": True}),
        _a("ast-p2-hoses", "loc-p2", "washer_hoses", "Washer hookup hoses (provided to tenants)", install_year=2016,
           material="rubber", notes="Landlord-provided washer hookup."),
        # P3 Saguaro Grill
        _a("ast-p3-ice", "loc-p3", "ice_maker_line", "Ice machine supply line", install_year=2019, material="braided steel"),
        _a("ast-p3-dish", "loc-p3", "dishwasher_line", "Commercial dishwasher supply line", install_year=2020),
        _a("ast-p3-ac", "loc-p3", "hvac_condensate", "Rooftop AC condensate lines (4 units)", last_service_date=date(2025, 11, 20)),
        _a("ast-p3-drains", "loc-p3", "roof_drains", "Roof drains and scuppers", last_service_date=date(2025, 5, 9),
           notes="Last cleared before the 2025 monsoon."),
        _a("ast-p3-rtu", "loc-p3", "rooftop_unit", "Rooftop AC units (4)", install_year=2016,
           notes="Straps and curbs last checked at install."),
        _a("ast-p3-wh", "loc-p3", "water_heater", "Commercial water heater (100 gal)", install_year=2018),
        # P4 Ponderosa
        _a("ast-p4-spk", "loc-p4", "sprinkler_system", "Wet sprinkler system", install_year=1996,
           last_service_date=date(2025, 10, 6), notes="Annual inspection. Riser in back stockroom, exterior wall."),
        _a("ast-p4-roof", "loc-p4", "roof", "Membrane roof (snow-load rated)", install_year=2004),
        _a("ast-p4-wh", "loc-p4", "water_heater", "Water heater (break room)", install_year=2013),
        _a("ast-p4-shutoff", "loc-p4", "main_shutoff", "Main water shutoff", notes="Back stockroom.", attributes={"location_confirmed": True}),
        # P5 Mesa Palms building-level
        _a("ast-p5-drains", "loc-p5", "roof_drains", "Roof drains and risers (all buildings)", last_service_date=date(2025, 6, 2)),
        _a("ast-p5-roof", "loc-p5", "roof", "Flat roof with internal drains", install_year=2011),
        _a("ast-p5-shutoff", "loc-p5", "main_shutoff", "Building shutoff valves (per floor)",
           notes="Shutoffs per floor and per unit; labelled 2022.", attributes={"location_confirmed": True}),
        # P6 Desert Bloom
        _a("ast-p6-cooler1", "loc-p6", "refrigeration", "Cooler room 1 compressor system", install_year=2009,
           last_service_date=date(2026, 8, 24)),
        _a("ast-p6-cooler2", "loc-p6", "refrigeration", "Cooler room 2 compressor system", install_year=2016,
           last_service_date=date(2025, 8, 19)),
        _a("ast-p6-gen", "loc-p6", "backup_power", "Standby generator (150 kW)", install_year=2014,
           last_service_date=date(2025, 8, 4), notes="Last load test August 2025."),
        _a("ast-p6-wash", "loc-p6", "wash_down_system", "Packing line wash-down water system", install_year=2009,
           last_service_date=date(2026, 3, 6)),
        _a("ast-p6-bf", "loc-p6", "backflow_preventer", "Backflow preventer on wash-down line", install_year=2017,
           last_service_date=date(2026, 3, 6)),
    ]
    # P5: 48 units, deterministic. Floor 1-4, letters A-L. Water heater years skew old in floors 3-4.
    rng = random.Random(rng_seed)
    for floor in range(1, 5):
        for letter in "ABCDEFGHIJKL":
            label = f"{floor}{letter}"
            wh = rng.choice([2008, 2011, 2013, 2015, 2017, 2019, 2021, 2023])
            if label in ("3B", "2B"):
                wh = 2014 if label == "3B" else 2020
            occupied = rng.random() > 0.08
            turnover = TODAY - timedelta(days=rng.randint(10, 700))
            out.append(_a(f"ast-p5-u{label}", "loc-p5", "unit", f"Unit {label}", unit_label=label, floor=floor,
                          attributes={"water_heater_year": wh, "occupied": occupied,
                                      "last_turnover_date": turnover.isoformat(),
                                      "supply_lines_checked_at_turnover": rng.random() > 0.5,
                                      "hvac_condensate_last_service": (TODAY - timedelta(days=rng.randint(30, 600))).isoformat(),
                                      "washer_hookup": rng.random() > 0.3},
                          notes="Unit register entry"))
    return out


def claims():
    return [
        {"id": "clm-p1-1", "policy_id": "pol-p1", "date": date(2023, 8, 14), "peril": "wind_hail",
         "cause": "Monsoon wind lifted roof tiles before purchase by current owner (prior-owner loss history)", "paid_usd": 4200},
        {"id": "clm-p2-1", "policy_id": "pol-p2", "date": date(2021, 5, 3), "peril": "water",
         "cause": "Water heater supply line failed between tenants; found after several days", "paid_usd": 6800},
        {"id": "clm-p3-1", "policy_id": "pol-p3", "date": date(2022, 9, 21), "peril": "liability",
         "cause": "Guest slipped on a wet entry floor after a monsoon roof leak", "paid_usd": 3500},
        {"id": "clm-p3-2", "policy_id": "pol-p3", "date": date(2024, 6, 30), "peril": "water",
         "cause": "Ice machine supply line leaked into dry storage over a weekend", "paid_usd": 11200},
        {"id": "clm-p4-1", "policy_id": "pol-p4", "date": date(2023, 1, 18), "peril": "freeze",
         "cause": "Stockroom pipe burst during a hard freeze while heat was set back", "paid_usd": 18400},
        {"id": "clm-p5-1", "policy_id": "pol-p5", "date": date(2024, 7, 9), "peril": "water",
         "cause": "Washer hose failure in an upper unit damaged the ceiling of the unit below", "paid_usd": 27900},
        {"id": "clm-p6-1", "policy_id": "pol-p6", "date": date(2022, 7, 26), "peril": "spoilage",
         "cause": "Compressor trip during an extreme-heat week; cooler warmed overnight", "paid_usd": 64000},
    ]


def _t(id, acct, rule, title, status, opened, closed, level=None, vis="private", asset=None):
    return {"id": id, "account_id": acct, "rule_id": rule, "title": title, "status": status,
            "opened_at": datetime.fromisoformat(opened), "closed_at": datetime.fromisoformat(closed),
            "proof_level": level, "visibility": vis, "asset_id": asset}


def task_history():
    return [
        _t("th-p1-2", "acct-p1", "az.ho.monsoon_roof_gutters.v1", "Clear gutters and check roof tiles before monsoon", "done",
           "2026-06-01T09:00:00", "2026-06-06T17:40:00", "E1", "shared"),
        _t("th-p2-1", "acct-p2", "az.ho.travel_vacancy_shutoff.v1", "Shut off the water and check for drips between tenants", "done",
           "2026-05-12T10:00:00", "2026-05-14T12:00:00", "E1", "shared"),
        _t("th-p2-2", "acct-p2", "az.ho.flash_flood_readiness.v1", "Flash-flood readiness and flood-coverage check", "declined",
           "2026-07-03T08:00:00", "2026-07-03T08:05:00"),
        _t("th-p3-1", "acct-p3", "az.bop.monsoon_roof_drains.v1", "Clear roof drains before monsoon", "done",
           "2026-06-02T08:00:00", "2026-06-09T11:00:00", "E1", "shared"),
        _t("th-p3-2", "acct-p3", "az.bop.wet_floor_response.v1", "Wet-floor response after a monsoon roof leak", "done",
           "2026-08-01T08:00:00", "2026-08-01T10:10:00", "E1", "shared"),
        _t("th-p3-3", "acct-p3", "az.bop.condensate_heat.v1", "Flush rooftop AC condensate lines", "expired",
           "2026-07-10T08:00:00", "2026-07-14T08:00:00"),
        _t("th-p4-1", "acct-p4", "az.bop.freeze_sprinkler_40f.v1", "Confirm thermostat 40°F+ near sprinkler riser", "done",
           "2026-01-09T14:00:00", "2026-01-09T14:30:00", "E2", "shared"),
        _t("th-p4-2", "acct-p4", "az.bop.holiday_closure.v1", "Holiday closure shutoff and heat checklist", "done",
           "2025-12-22T10:00:00", "2025-12-23T16:00:00", "E2", "shared"),
        _t("th-p5-1", "acct-p5", "az.cre.unit_register.v1", "Complete the unit register", "done",
           "2026-03-10T09:00:00", "2026-03-24T15:00:00", "E2", "shared"),
        _t("th-p5-2", "acct-p5", "az.cre.risers_roof_drains.v1", "Inspect risers and roof drains before monsoon", "done",
           "2026-06-01T09:00:00", "2026-06-02T16:00:00", "E2", "shared"),
        _t("th-p5-3", "acct-p5", "az.cre.turnover_supply_lines.v1", "Supply-line check at Unit 4F turnover", "done",
           "2026-08-12T09:00:00", "2026-08-13T13:00:00", "E1", "shared"),
        _t("th-p6-1", "acct-p6", "az.ag.preharvest_refrigeration.v1", "Service refrigeration before harvest", "done",
           "2026-08-18T07:00:00", "2026-08-26T16:00:00", "E3", "shared", "ast-p6-cooler1"),
        _t("th-p6-2", "acct-p6", "az.ag.washdown_backflow.v1", "Wash-down hose and backflow check", "done",
           "2026-03-01T07:00:00", "2026-03-06T15:00:00", "E3", "shared", "ast-p6-wash"),
    ]


def devices():
    return [
        {"id": "dev-p1-main", "location_id": "loc-p1", "model": "Simulated whole-home flow & leak monitor",
         "label": "Main line monitor", "supports_shutoff": True},
        {"id": "dev-p1-laundry", "location_id": "loc-p1", "model": "Simulated leak puck",
         "label": "Laundry room leak sensor", "supports_shutoff": False},
        {"id": "dev-p5-3b", "location_id": "loc-p5", "model": "Simulated unit leak sensor + valve",
         "label": "Unit 3B kitchen/laundry sensor", "unit_label": "3B", "supports_shutoff": True},
        {"id": "dev-p5-2b", "location_id": "loc-p5", "model": "Simulated unit leak sensor + valve",
         "label": "Unit 2B sensor", "unit_label": "2B", "supports_shutoff": True},
        {"id": "dev-p5-riser", "location_id": "loc-p5", "model": "Simulated riser flow monitor",
         "label": "Building B riser flow", "supports_shutoff": True},
        {"id": "dev-p6-cooler1", "location_id": "loc-p6", "model": "Simulated cooler temperature probe",
         "label": "Cooler room 1 temperature", "kind": "cooler", "supports_shutoff": False},
        {"id": "dev-p4-riser", "location_id": "loc-p4", "model": "Simulated stockroom temperature probe",
         "label": "Stockroom temperature", "kind": "stockroom", "supports_shutoff": False},
    ]
