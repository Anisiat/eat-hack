"""Step 4: the month plan.

Rank the month's events by best-lineup QRP per pound, with a bonus for boroughs where WatchHumans has
few users, and fill RGC's capacity with no two pop-ups on the same day. Each pop-up keeps its best
lineup: clients do not pay RGC for pop-up placement, so no brand is guaranteed a slot.
The habit plan is RGC's usual five at the month's biggest events.
"""
BOROUGH_BONUS = 0.2


def borough_bonus(boroughs):
    x = boroughs.set_index("borough")["watchhumans_users_per_1000"]
    z = ((x.mean() - x) / x.std()).clip(0, 2)          # only under-covered boroughs get a bonus
    return (1 + BOROUGH_BONUS * z).to_dict()


def month_plan(d, opt, events, lineups, month, capacity):
    in_month = [i for i in range(len(events)) if events["start"].iloc[i].strftime("%Y-%m") == month]
    assert in_month, f"no events in {month}"
    bonus = borough_bonus(d["boroughs"])
    eid = events["event_id"].to_numpy()
    rank = sorted(in_month, key=lambda i: -lineups[eid[i]]["qrp"] / max(events["cost"].iloc[i], 1)
                  * bonus.get(events["borough"].iloc[i], 1.0))
    chosen, days = [], set()
    for i in rank:
        if len(chosen) == capacity:
            break
        if events["date"].iloc[i] not in days:
            chosen.append(i)
            days.add(events["date"].iloc[i])
    chosen.sort(key=lambda i: events["start"].iloc[i])

    # each event keeps its own best lineup; brands are not guaranteed a slot (clients do not pay for one)
    lu = {i: [opt.bids.index(b) for b in lineups[eid[i]]["brands"]] for i in chosen}

    popups = []
    for i in chosen:
        res = opt.evaluate(i, lu[i])
        popups.append(dict(event_id=eid[i], name=events["name"].iloc[i], date=events["date"].iloc[i],
                           event_type=events["event_type"].iloc[i], borough=events["borough"].iloc[i],
                           brands=[opt.bids[j] for j in lu[i]], qrp=round(res["qrp"], 1),
                           cost=round(float(events["cost"].iloc[i]), 2),
                           borough_bonus=round(bonus.get(events["borough"].iloc[i], 1.0), 3)))

    # habit: the usual five at the biggest events of the month
    habit, hdays = [], set()
    for i in sorted(in_month, key=lambda i: -events["footfall"].iloc[i]):
        if len(habit) == capacity:
            break
        if events["date"].iloc[i] not in hdays:
            habit.append(i)
            hdays.add(events["date"].iloc[i])
    habit_qrp = sum(opt.evaluate(i, opt.habit)["qrp"] for i in habit)
    habit_cost = float(sum(events["cost"].iloc[i] for i in habit))

    total_qrp = sum(p["qrp"] for p in popups)
    total_cost = sum(p["cost"] for p in popups)
    covered = sorted({b for p in popups for b in p["brands"]})
    return dict(month=month, capacity=capacity, popups=popups,
                total_qrp=round(total_qrp, 1), total_cost=round(total_cost, 2),
                cost_per_qr=round(total_cost / total_qrp, 2) if total_qrp else None,
                habit_events=[eid[i] for i in habit], habit_total_qrp=round(habit_qrp, 1),
                habit_total_cost=round(habit_cost, 2),
                habit_cost_per_qr=round(habit_cost / habit_qrp, 2) if habit_qrp else None,
                uplift_vs_habit=round(total_qrp / habit_qrp - 1, 3) if habit_qrp else None,
                brands_featured=len(covered), brands_not_featured=sorted(set(opt.bids) - set(covered)))
