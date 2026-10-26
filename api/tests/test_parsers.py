import gzip
from datetime import date

from history_stats import build_history, year_stats
from nri_parse import area_block, percentile_rank
from storm_parse import is_monsoon, parse_damage, parse_ncei_date, read_events, summarize


def test_parse_damage():
    assert parse_damage("10.00K") == 10000 and parse_damage("1.5M") == 1_500_000
    assert parse_damage("2B") == 2e9 and parse_damage("0") == 0 and parse_damage("") == 0
    assert parse_damage(None) == 0 and parse_damage("abc") == 0


def test_parse_ncei_date():
    assert parse_ncei_date("15-JUL-21 16:30:00") == "2021-07-15"
    assert parse_ncei_date("01-JAN-99 00:00:00") == "1999-01-01"
    assert parse_ncei_date("garbage") is None


def test_monsoon_window():
    assert is_monsoon("2024-06-15") and is_monsoon("2024-09-30")
    assert not is_monsoon("2024-06-14") and not is_monsoon("2024-10-01")


def _csv(rows):
    head = ("EVENT_ID,STATE,CZ_NAME,EVENT_TYPE,BEGIN_DATE_TIME,CZ_TYPE,CZ_FIPS,INJURIES_DIRECT,"
            "DEATHS_DIRECT,DAMAGE_PROPERTY,DAMAGE_CROPS,MAGNITUDE,MAGNITUDE_TYPE,FLOOD_CAUSE\n")
    return gzip.compress((head + "\n".join(rows) + "\n").encode())


def test_read_events_filters_state_and_summarizes():
    raw = _csv([
        "1,ARIZONA,MARICOPA,Flash Flood,15-JUL-21 16:30:00,C,13,0,0,25.00K,0,,,Heavy Rain",
        "2,ARIZONA,MARICOPA,Hail,02-MAR-21 10:00:00,C,13,1,0,1.00M,0,1.25,EG,",
        "3,TEXAS,HARRIS,Hail,02-MAR-21 10:00:00,C,201,0,0,0,0,,,",
    ])
    ev = read_events(raw, "ARIZONA", set())
    assert len(ev) == 2
    s = summarize(ev)
    assert s["total_events"] == 2 and s["monsoon_season_by_type"] == {"Flash Flood": 1}
    assert s["property_damage_usd"] == 1_025_000 and s["injuries"] == 1


def _rows(year, temps, precip=0.0):
    return [{"date": date(year, 7, 1 + i), "tmax": t, "tmin": t - 25, "precip": precip}
            for i, t in enumerate(temps)]


def test_year_stats_heat_and_streaks():
    s = year_stats(_rows(2024, [112, 111, 100, 115, 110]))
    assert s["days_ge_110f"] == 4 and s["days_ge_115f"] == 1 and s["longest_streak_ge_110f"] == 2
    assert s["max_temp_f"] == 115 and s["monsoon_days_ge_050in"] == 0


def test_year_stats_monsoon_precip_and_freeze():
    rows = [{"date": date(2024, 7, 4), "tmax": 100, "tmin": 80, "precip": 0.6},
            {"date": date(2024, 1, 4), "tmax": 40, "tmin": 25, "precip": 0.1}]
    s = year_stats(rows)
    assert s["monsoon_precip_in"] == 0.6 and s["monsoon_days_ge_050in"] == 1
    assert s["nights_le_28f"] == 1 and s["nights_le_32f"] == 1
    assert s["wettest_day"] == {"date": "2024-07-04", "precip_in": 0.6}


def test_build_history_normals_and_averages():
    rows = _rows(2021, [110, 100]) + _rows(2022, [112, 90])
    h = build_history(rows, [2021, 2022], (2021, 2022))
    assert h["avg_per_year"]["days_ge_110f"] == 1.0
    assert h["monthly_normals"][0]["month"] == 7


def test_nri_helpers():
    assert percentile_rank(50, [10, 20, 60, 70]) == 50.0
    assert percentile_rank(None, [1]) is None and percentile_rank(1, []) is None
    block = area_block({"POPULATION": "1000", "HWAV_EALS": "88.5", "HWAV_EALR": "Very High", "HWAV_EALT": ""})
    assert block["hazards"]["HWAV"]["eal_score"] == 88.5 and block["hazards"]["HWAV"]["eal_total_usd"] is None
