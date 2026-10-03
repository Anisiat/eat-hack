"""
build_event_types.py - the crowd table as data: one row per event type.

Writes event_types.csv (repo root by default):
  event_type, need_* (8), mix_* (5 assumed audience shares), indoor_share, dwell_hours, staff, peak_slot, moment

Need states and audience mix are the public starting assumptions from the crowd table in eat_hack.md,
shared with generate_popups.EVENT. Only those assumptions are copied; no hidden truth.

Run:  python scripts/build_event_types.py [output_folder]
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_popups import EVENT, EVENT_TYPES, NEEDS, SEGMENTS  # noqa: E402

# peak-need moment per type: when to be at the stall, and what is happening then
MOMENT = {
    "community": ("11:00-13:00", "Browsing the market, or lingering after the run club"),
    "concerts": ("21:00-23:00", "Late in a hot room, between sets"),
    "conferences": ("15:00-16:30", "Mid-afternoon slump at the desks"),
    "expos": ("12:00-14:00", "Lunchtime browsing between stalls"),
    "festivals": ("14:00-17:00", "Afternoon heat, walking and queues"),
    "performing_arts": ("interval", "Interval drinks and a sweet treat"),
    "sports": ("finish", "Just finished or full time, rehydrating and refuelling"),
}


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
    rows = []
    for t in EVENT_TYPES:
        p = EVENT[t]
        row = dict(event_type=t)
        row.update({f"need_{n}": float(v) for n, v in zip(NEEDS, p["needs"])})
        row.update({f"mix_{s}": float(v) for s, v in zip(SEGMENTS, p["mix"])})
        row.update(indoor_share=p["indoor"], dwell_hours=p["dwell"], staff=p["staff"],
                   peak_slot=MOMENT[t][0], moment=MOMENT[t][1])
        rows.append(row)
    pd.DataFrame(rows).to_csv(out_dir / "event_types.csv", index=False)
    print(f"Wrote {len(rows)} event types to {out_dir}/event_types.csv")


if __name__ == "__main__":
    main()
