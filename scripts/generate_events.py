"""
generate_events.py - PLACEHOLDER upcoming London events for Pop-up Pick.

Writes events.csv (repo root by default): 36 events, Oct to Dec 2026, in the final schema:
  event_id, name, event_type, start, end, venue, borough, lat, lon, expected_attendance, indoor,
  audience_tags, stall_cost_gbp, link, source

Venues are real public places with approximate coordinates; the events themselves are invented
(source = placeholder). Replace this file with hand-collected real listings, same columns.

Run:  python scripts/generate_events.py [output_folder]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_popups import EVENT, EVENT_TYPES, SEGMENTS  # noqa: E402

SEED = 7
N_EVENTS = 36
FIRST, LAST = pd.Timestamp("2026-10-05"), pd.Timestamp("2026-12-20")

# (venue, borough, lat, lon, indoor)
VENUES = {
    "sports": [("Battersea Park", "Wandsworth", 51.4791, -0.1569, 0), ("Victoria Park", "Tower Hamlets", 51.5362, -0.0396, 0),
               ("Bushy Park", "Richmond upon Thames", 51.4104, -0.3363, 0), ("Wembley Park", "Brent", 51.5560, -0.2796, 0),
               ("Big-screen pub, Brixton", "Lambeth", 51.4613, -0.1156, 1), ("Big-screen bar, Shoreditch", "Hackney", 51.5246, -0.0784, 1)],
    "community": [("Maltby Street Market", "Southwark", 51.4996, -0.0757, 0), ("Broadway Market", "Hackney", 51.5367, -0.0618, 0),
                  ("Brockley Market", "Lewisham", 51.4628, -0.0369, 0), ("Walthamstow Village", "Waltham Forest", 51.5826, -0.0137, 0),
                  ("Surrey Street Market", "Croydon", 51.3714, -0.1013, 0), ("Ealing Common", "Ealing", 51.5091, -0.2888, 0),
                  ("Islington community hall", "Islington", 51.5416, -0.1022, 1)],
    "concerts": [("Electric Brixton", "Lambeth", 51.4614, -0.1146, 1), ("O2 Forum Kentish Town", "Camden", 51.5524, -0.1416, 1),
                 ("Village Underground", "Hackney", 51.5243, -0.0778, 1), ("Eventim Apollo", "Hammersmith and Fulham", 51.4908, -0.2246, 1)],
    "conferences": [("Shoreditch co-working space", "Hackney", 51.5265, -0.0798, 1), ("Here East", "Newham", 51.5466, -0.0226, 1),
                    ("Barbican Centre", "City of London", 51.5202, -0.0938, 1), ("King's Cross tech campus", "Camden", 51.5347, -0.1246, 1),
                    ("Canary Wharf conference centre", "Tower Hamlets", 51.5054, -0.0235, 1)],
    "expos": [("ExCeL London", "Newham", 51.5081, 0.0294, 1), ("Olympia London", "Hammersmith and Fulham", 51.4963, -0.2105, 1),
              ("University students' union, Bloomsbury", "Camden", 51.5246, -0.1340, 1),
              ("University campus, Mile End", "Tower Hamlets", 51.5246, -0.0400, 1)],
    "festivals": [("Clapham Common", "Lambeth", 51.4603, -0.1496, 0), ("Queen Elizabeth Olympic Park", "Newham", 51.5430, -0.0164, 0),
                  ("Greenwich Peninsula", "Greenwich", 51.5003, 0.0037, 0), ("Finsbury Park", "Haringey", 51.5713, -0.1035, 0)],
    "performing_arts": [("Southbank Centre", "Lambeth", 51.5058, -0.1167, 1), ("West End theatre", "Westminster", 51.5115, -0.1300, 1),
                        ("Camden comedy club", "Camden", 51.5390, -0.1426, 1), ("Hackney Empire", "Hackney", 51.5459, -0.0554, 1),
                        ("Richmond Theatre", "Richmond upon Thames", 51.4612, -0.3036, 1)],
}
NAMES = {
    "sports": [],   # see RACES and SCREENINGS
    "community": ["Weekend food market", "Run club social and brunch", "Family fun day", "Makers' and food market",
                  "Christmas community market"],
    "concerts": ["Live gig", "Club night", "Indie double bill", "DJ all-nighter"],
    "conferences": ["Weekend AI hackathon", "Student hackathon", "Startup summit", "Tech meetup and demo night"],
    "expos": ["Food and drink expo", "Lifestyle show", "Refreshers' fair", "Graduate careers fair"],
    "festivals": ["Autumn food festival", "Bonfire night festival", "Winter street food festival"],
    "performing_arts": ["Comedy night", "Contemporary dance show", "Theatre premiere", "Christmas panto"],
}
RACES = ["Autumn 10K", "Park half marathon", "Saturday 5K series", "Cross-country relay"]
SCREENINGS = ["Big-match screening", "Rugby international screening"]
# events per type in the placeholder month window (outdoor festivals are rare in winter)
COUNTS = {"sports": 6, "community": 8, "concerts": 4, "conferences": 5, "expos": 4, "festivals": 3,
          "performing_arts": 6}


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    rng = np.random.default_rng(SEED)
    assert sum(COUNTS.values()) == N_EVENTS and set(COUNTS) == set(EVENT_TYPES)
    days = pd.date_range(FIRST, LAST)
    rows = []
    for t, n in COUNTS.items():
        p = EVENT[t]
        for _ in range(n):
            venue, borough, lat, lon, indoor = VENUES[t][rng.integers(len(VENUES[t]))]
            names, weekdays, times = NAMES[t], p["days"], p["start"]
            if t == "sports":   # outdoor venues host weekend races, indoor venues host evening screenings
                names, weekdays, times = (SCREENINGS, [1, 2, 5], ["19:45"]) if indoor else (RACES, [5, 6], ["09:00"])
            d = rng.choice([x for x in days if x.weekday() in weekdays])
            start = pd.Timestamp(f"{pd.Timestamp(d).date()} {times[rng.integers(len(times))]}")
            end = start + pd.Timedelta(hours=p["dwell"])
            lo, hi = p["footfall"]
            mix = p["mix"] * rng.uniform(.7, 1.3, len(SEGMENTS))
            tags = [s for s, _ in sorted(zip(SEGMENTS, mix), key=lambda x: -x[1])[:2]]
            stall = 0 if p["stall"][1] == 0 else int(round(rng.integers(p["stall"][0], p["stall"][1] + 1), -1))
            rows.append(dict(name=f"{names[rng.integers(len(names))]}, {venue}", event_type=t,
                             start=start.isoformat(timespec="minutes"), end=end.isoformat(timespec="minutes"),
                             venue=venue, borough=borough, lat=lat, lon=lon,
                             expected_attendance=int(round(rng.integers(lo, hi + 1), -1)), indoor=indoor,
                             audience_tags="|".join(tags), stall_cost_gbp=stall, link="", source="placeholder"))
    df = pd.DataFrame(rows).sort_values("start", kind="stable").reset_index(drop=True)
    df.insert(0, "event_id", [f"E{i + 1:03d}" for i in range(len(df))])
    df.to_csv(out_dir / "events.csv", index=False)
    print(f"Wrote {len(df)} placeholder events ({df['start'].min()[:10]} to {df['start'].max()[:10]}) "
          f"to {out_dir}/events.csv")


if __name__ == "__main__":
    main()
