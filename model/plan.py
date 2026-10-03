"""Step 4: the month plan.

Rank the month's events (UK-wide) by expected net value in pounds, skip events that are likely to lose money, and fill RGC's capacity with no two pop-ups on the same day.
Each pop-up keeps its best lineup: clients do not pay RGC for pop-up placement, so no brand is guaranteed a slot.
The habit plan is RGC's usual lineup at the month's biggest events.
"""
from .value import time_saved

MAX_P_WASTE = 0.5       # skip events more likely than not to lose money


def _pick(order, events, capacity):
    chosen, days = [], set()
    for i in order:
        if len(chosen) == capacity:
            break
        if events["date"].iloc[i] not in days:
            chosen.append(i)
            days.add(events["date"].iloc[i])
    return sorted(chosen, key=lambda i: events["start"].iloc[i])


def month_plan(d, opt, events, lineups, month, capacity, A):
    in_month = [i for i in range(len(events)) if events["start"].iloc[i].strftime("%Y-%m") == month]
    assert in_month, f"no events in {month}"
    eid = events["event_id"].to_numpy()
    worth_it = [i for i in in_month
                if lineups[eid[i]]["value"]["net_value"] > 0 and lineups[eid[i]]["value"]["p_waste"] <= MAX_P_WASTE]
    rank = sorted(worth_it, key=lambda i: -lineups[eid[i]]["value"]["net_value"])
    chosen = _pick(rank, events, capacity)

    popups = []
    for i in chosen:
        lu = lineups[eid[i]]
        popups.append(dict(event_id=eid[i], name=lu["name"], date=lu["date"], event_type=lu["event_type"],
                           km_from_london=lu["km_from_london"], expected_attendance=lu["expected_attendance"],
                           brands=lu["brands"], exp_reviews=lu["exp_reviews"], exp_signups=lu["exp_signups"],
                           net_value=lu["value"]["net_value"], p_waste=lu["value"]["p_waste"]))

    # habit: the usual lineup at the biggest events of the month, worth it or not
    habit = _pick(sorted(in_month, key=lambda i: -events["footfall"].iloc[i]), events, capacity)
    hv = [lineups[eid[i]]["habit_value"] for i in habit]

    covered = sorted({b for p in popups for b in p["brands"]})
    t = time_saved(A)
    net, habit_net = sum(p["net_value"] for p in popups), sum(v["net_value"] for v in hv)
    return dict(month=month, capacity=capacity, popups=popups,
                exp_reviews=round(sum(p["exp_reviews"] for p in popups), 1),
                net_value=round(net, 2),
                habit_events=[eid[i] for i in habit],
                habit_exp_reviews=round(sum(lineups[eid[i]]["habit_exp_reviews"] for i in habit), 1),
                habit_net_value=round(habit_net, 2),
                habit_expected_wasted=round(sum(v["p_waste"] for v in hv), 2),
                skipped_events=len(in_month) - len(worth_it),
                marketing_hours_saved=round(t["hours_per_month"], 1),
                marketing_time_saved_gbp=round(t["gbp_per_month"], 2),
                month_gain_gbp=round(net - habit_net + t["gbp_per_month"], 2),
                brands_featured=len(covered), brands_not_featured=sorted(set(opt.bids) - set(covered)))
