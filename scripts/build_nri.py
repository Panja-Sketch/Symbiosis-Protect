"""FEMA National Risk Index (Dec 2025, v1.20) -> data/derived/nri_az.json (county + tract per location)."""

import csv
import zipfile

from lib import DERIVED, RAW, download, load_locations, write_json
from nri_parse import HAZARDS, area_block, percentile_rank

BASE = "https://www.fema.gov/about/reports-and-data/openfema/nri/v120/"
csv.field_size_limit(2**30)


def az_rows(zip_path, member):
    with zipfile.ZipFile(zip_path) as z, z.open(member) as f:
        import io
        for row in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
            if row["STATEABBRV"] == "AZ":
                yield row


def main():
    counties_zip = download(BASE + "NRI_Table_Counties.zip", RAW / "nri_counties.zip")
    tracts_zip = download(BASE + "NRI_Table_CensusTracts.zip", RAW / "nri_tracts.zip")
    counties = {r["STCOFIPS"]: r for r in az_rows(counties_zip, "NRI_Table_Counties.csv")}
    tracts = {r["TRACTFIPS"]: r for r in az_rows(tracts_zip, "NRI_Table_CensusTracts.csv")}
    print("AZ counties", len(counties), "AZ tracts", len(tracts))
    az_tract_eal = {c: [float(r[f"{c}_EALS"]) for r in tracts.values() if r.get(f"{c}_EALS")]
                    for c in HAZARDS}
    out = {"provenance": "HISTORIC", "source": "FEMA National Risk Index, December 2025 (v1.20)",
           "source_url": "https://hazards.fema.gov/nri/", "notes": (
               "eal_score is a national percentile (0-100). az_tract_percentile ranks the tract's "
               "score among all Arizona tracts. NRI v1.20 names the riverine flood hazard Inland "
               "Flooding (IFLD); the spec's RFLD prefix does not exist in this release."), "locations": {}}
    for loc in load_locations():
        t, c = tracts.get(loc["fema_tract_id"]), counties[loc["county_fips"]]
        entry = {"county": area_block(c), "tract": area_block(t) if t else None,
                 "tract_id": loc["fema_tract_id"], "county_fips": loc["county_fips"]}
        if t:
            for code, hz in entry["tract"]["hazards"].items():
                hz["az_tract_percentile"] = percentile_rank(hz["eal_score"], az_tract_eal[code])
        out["locations"][loc["id"]] = entry
        top = sorted(((h["name"], h["eal_rating"]) for h in (entry["tract"] or entry["county"])["hazards"].values()
                      if h["eal_score"] is not None), key=lambda x: x[0])
        print(loc["id"], bool(t), (entry["tract"] or entry["county"])["risk_rating"], top[:3])
    write_json(DERIVED / "nri_az.json", out)


if __name__ == "__main__":
    main()
