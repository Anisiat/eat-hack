"""
get_borough_census.py - real Census 2021 population and age profile for the 33 London boroughs.

Source: ONS Census 2021, TS007 Age by single year (Nomis dataset NM_2027_1), usual residents.
Writes data/raw/borough_census_2021.csv:
  borough, ons_code, inner_outer, population_2021, pop_18_34, share_18_34

Run:  python scripts/get_borough_census.py
"""
import io
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "borough_census_2021.csv"

# Nomis age codes: 0 = all usual residents; code n = "Aged n-1 years", so 19..35 = ages 18..34
URL = ("https://www.nomisweb.co.uk/api/v01/dataset/NM_2027_1.data.csv"
       "?geography=TYPE154&c2021_age_102=0,19...35&measures=20100"
       "&select=geography_name,geography_code,c2021_age_102,obs_value")

# ONS statistical definition of Inner London
INNER = {"Camden", "City of London", "Hackney", "Hammersmith and Fulham", "Haringey", "Islington",
         "Kensington and Chelsea", "Lambeth", "Lewisham", "Newham", "Southwark", "Tower Hamlets",
         "Wandsworth", "Westminster"}


def main():
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    df = df[df["GEOGRAPHY_CODE"].str.startswith("E09")]          # London boroughs + City
    total = df[df["C2021_AGE_102"] == 0].set_index("GEOGRAPHY_CODE")
    young = df[df["C2021_AGE_102"] != 0].groupby("GEOGRAPHY_CODE")["OBS_VALUE"].sum()

    out = pd.DataFrame({
        "borough": total["GEOGRAPHY_NAME"],
        "ons_code": total.index,
        "population_2021": total["OBS_VALUE"].astype(int),
        "pop_18_34": young.reindex(total.index).astype(int),
    }).reset_index(drop=True)
    out.insert(2, "inner_outer", out["borough"].map(lambda b: "inner" if b in INNER else "outer"))
    out["share_18_34"] = (out["pop_18_34"] / out["population_2021"]).round(4)
    out = out.sort_values("borough").reset_index(drop=True)

    assert len(out) == 33, f"expected 33 London boroughs, got {len(out)}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"Wrote {len(out)} boroughs, London population {out['population_2021'].sum():,} to {OUT}")


if __name__ == "__main__":
    main()
