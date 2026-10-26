"""Resolve NWS zone/county, census tract, elevation for the 6 persona locations -> data/seed/locations.json."""

from lib import SEED, get_json, write_json

# (id, account, label, city, county, lat, lon, hard_water)  — real city coords, slightly jittered, fictional streets.
BASE = [
    ("loc-p1", "acct-p1", "Maya's home (Chandler)", "Chandler", "Maricopa", 33.3062, -111.8413, True),
    ("loc-p2", "acct-p2", "Luis's rental (Tucson)", "Tucson", "Pima", 32.2226, -110.9747, True),
    ("loc-p3", "acct-p3", "Saguaro Grill (Tempe)", "Tempe", "Maricopa", 33.4255, -111.9400, True),
    ("loc-p4", "acct-p4", "Ponderosa Outfitters (Flagstaff)", "Flagstaff", "Coconino", 35.1983, -111.6513, False),
    ("loc-p5", "acct-p5", "Mesa Palms Apartments (Mesa)", "Mesa", "Maricopa", 33.4152, -111.8315, True),
    ("loc-p6", "acct-p6", "Desert Bloom Produce (Yuma)", "Yuma", "Yuma", 32.6927, -114.6277, True),
]
JITTER = [(0.0021, -0.0017), (-0.0013, 0.0024), (0.0009, 0.0011), (-0.0018, -0.0012), (0.0015, 0.0020),
          (-0.0022, 0.0008)]


def main():
    out = []
    for (lid, acct, label, city, county, lat, lon, hard), (dy, dx) in zip(BASE, JITTER):
        lat, lon = round(lat + dy, 4), round(lon + dx, 4)
        pt = get_json(f"https://api.weather.gov/points/{lat},{lon}")["properties"]
        fcc = get_json("https://geo.fcc.gov/api/census/block/find",
                       {"latitude": lat, "longitude": lon, "format": "json"})
        elev = get_json("https://api.open-meteo.com/v1/elevation", {"latitude": lat, "longitude": lon})
        out.append({
            "id": lid, "account_id": acct, "label": label, "city": city, "county": county + " County",
            "state": "AZ", "lat": lat, "lon": lon,
            "nws_zone": pt["forecastZone"].rsplit("/", 1)[-1],
            "nws_county": pt["county"].rsplit("/", 1)[-1],
            "nws_office": pt["gridId"], "nws_grid_x": pt["gridX"], "nws_grid_y": pt["gridY"],
            "time_zone": pt["timeZone"],
            "county_fips": fcc["County"]["FIPS"], "fema_tract_id": fcc["Block"]["FIPS"][:11],
            "elevation_ft": round(elev["elevation"][0] * 3.28084),
            "hard_water_zone": hard,
            "provenance": "SYNTHETIC",
        })
        print(lid, out[-1]["nws_zone"], out[-1]["fema_tract_id"], out[-1]["elevation_ft"])
    write_json(SEED / "locations.json", out)


if __name__ == "__main__":
    main()
