"""Run the Pop-up Pick model end to end and write outputs/.

  python -m model.run [--month 2026-12] [--capacity 2]

Writes outputs/scores.csv, lineups.json, profiles.json, impact.json, month_plan.json.
Headline: net value per pop-up in pounds (data/assumptions/value_assumptions.csv), from sign-ups, reviews and publicity
"""
import argparse
import json

import numpy as np
import pandas as pd

from . import fit as fitmod
from . import outcomes, plan, profiles
from .data import ARCHETYPES, OUT, load, past_events, upcoming_events
from .impact import uplift_test
from .value import load_assumptions, p_waste, rounded, value
from .optimise import MAX_CHILLED, NO_ADULTS, Optimiser, lineup_reasons


def to_json(obj, path):
    def default(o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        raise TypeError(type(o))
    path.write_text(json.dumps(obj, indent=2, default=default, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default="2026-12")
    ap.add_argument("--capacity", type=int, default=2)   # RGC runs 2 pop-ups a month
    args = ap.parse_args()

    d = load()
    A = load_assumptions()
    past = past_events(d)
    events = upcoming_events(d)

    # 1-2. fit and outcome models, trained on the 48 training pop-ups
    fm = fitmod.train(d)
    om = outcomes.train(d, past, fitmod.score(d, fm, past))

    # 3. best lineup per upcoming event
    parts = fitmod.score(d, fm, events)
    opt = Optimiser(d, om, events, parts)
    brand_reason = lambda i, j: fitmod.reasons(d, fm, events, parts, i, j)  # noqa: E731
    lineups, score_rows = {}, []
    for i, e in enumerate(events.itertuples()):
        best, _ = opt.best(i)
        res = opt.evaluate(i, best)
        habit = opt.evaluate(i, opt.habit_for(i))
        tool_v, habit_v = money(opt, i, best, res, e.cost, A), money(opt, i, opt.habit_for(i), habit, e.cost, A)
        lineups[e.event_id] = dict(
            name=e.name, date=e.date, event_type=e.event_type, category=e.category,
            latitude=float(e.latitude), longitude=float(e.longitude), km_from_london=float(e.km_from_london),
            family_event=bool(e.family_event), expected_attendance=int(e.footfall), lineup_size=len(best),
            brands=[opt.bids[j] for j in best],
            brand_names=[d["brands"].at[opt.bids[j], "brand_name"] for j in best],
            products={opt.bids[j]: d["products"].iloc[parts["best_product"][i, j]]["product"] for j in best},
            units={opt.bids[j]: int(opt.units[i, j]) for j in best}, slot=opt.slot(i),
            archetype_mix={a: round(float(v), 3) for a, v in zip(ARCHETYPES, parts["mix"][i])},
            match=round(res["match"], 3), exp_signups=round(res["signups"], 1), exp_reviews=round(res["reviews"], 1),
            value=tool_v,
            habit_brands=[opt.bids[j] for j in opt.habit_for(i)], habit_match=round(habit["match"], 3),
            habit_exp_reviews=round(habit["reviews"], 1), habit_value=habit_v,
            reasons=lineup_reasons(d, opt, i, best, res, habit, brand_reason),
            **ui_extras(d, opt, parts, events, i, best, res))
        # brand-level scores in the context of the best lineup's sign-ups
        s = res["signups"]
        for j, bid in enumerate(opt.bids):
            rs = brand_reason(i, j)
            score_rows.append(dict(event_id=e.event_id, brand_id=bid,
                                   best_product_id=d["products"].iloc[parts["best_product"][i, j]]["product_id"],
                                   product=d["products"].iloc[parts["best_product"][i, j]]["product"],
                                   match=round(float(parts["match"][i, j]), 4), fit=round(float(parts["fit"][i, j]), 4),
                                   exp_signups=round(s, 1), exp_reviews=round(s * opt.r[i, j], 2),
                                   in_best_lineup=int(j in best),
                                   reason_1=rs[0], reason_2=rs[1], reason_3=rs[2]))
    scores = pd.DataFrame(score_rows)

    # 4. month plan
    month = plan.month_plan(d, opt, events, lineups, args.month, args.capacity, A)

    # 5. brand profiles
    profs = profiles.build(d, fm, scores, events)

    # uplift on the 12 held-out pop-ups
    test = past[past["split"] == "test"]
    impact = uplift_test(d, Optimiser(d, om, test, fitmod.score(d, fm, test)), test, A)
    impact["poisson_test_deviance"] = round(om.test_deviance, 3)
    impact["footfall_baseline_test_deviance"] = round(om.baseline_deviance, 3)

    check(d, events, scores, lineups, profs, impact, A)

    OUT.mkdir(exist_ok=True)
    scores.to_csv(OUT / "scores.csv", index=False)
    to_json(lineups, OUT / "lineups.json")
    to_json(profs, OUT / "profiles.json")
    to_json(impact, OUT / "impact.json")
    to_json(month, OUT / "month_plan.json")
    to_json(event_audience(events, parts), OUT / "event_audience.json")

    nv = np.mean([v["value"]["net_value"] for v in lineups.values()])
    hv = np.mean([v["habit_value"]["net_value"] for v in lineups.values()])
    print(f"{len(events)} events (under {A['max_attendance']:.0f} people) x {len(opt.bids)} brands scored. "
          f"Mean net value per pop-up: tool £{nv:.0f}, usual lineup £{hv:.0f}")
    print(f"Held-out pop-ups: reviews {impact['review_uplift']:+.1%} (95% CI {impact['review_ci_low']:+.1%} to "
          f"{impact['review_ci_high']:+.1%}); net value £{impact['net_value_tool']:.0f} vs £{impact['net_value_habit']:.0f} "
          f"per pop-up; wasted pop-ups {impact['waste_rate_tool']:.0%} vs {impact['waste_rate_habit']:.0%}")
    print(f"Monthly impact £{impact['monthly_impact_gbp']:.0f} (better lineups £{impact['monthly_lineup_gain_gbp']:.0f}, "
          f"marketing time £{impact['monthly_time_saved_gbp']:.0f} = {impact['monthly_hours_saved']:.0f} h)")
    print(f"Sign-up model test deviance {om.test_deviance:.2f} vs footfall baseline {om.baseline_deviance:.2f}")
    print(f"Month plan {month['month']}: {len(month['popups'])} pop-ups, net value £{month['net_value']:.0f} "
          f"vs usual £{month['habit_net_value']:.0f}; {month['skipped_events']} events skipped as likely losses")
    print(f"Wrote outputs to {OUT}/")


STALL_SIZES = {"small": 0.6, "medium": 1.0, "large": 1.5}     # units multiplier per stall size


def ui_extras(d, opt, parts, events, i, best, res):
    """Extra fields the PopUpPick website shows; all computed here, never in the browser."""
    e = events.iloc[i]
    b = d["brands"]
    prod = {opt.bids[j]: d["products"].iloc[parts["best_product"][i, j]] for j in best}
    per_arch = parts["per_arch"][i, best]                                   # lineup x archetypes
    winner = {a: prod[opt.bids[best[k]]]["product_id"] for a, k in zip(ARCHETYPES, per_arch.argmax(0))}
    restricted = bool(e["event_type"] in NO_ADULTS or e["family_event"])
    lb = b.loc[[opt.bids[j] for j in best]]
    stops = opt.stops[i]
    units_by_size = {opt.bids[j]: {k: int(min(np.ceil(stops * f * 1.2), opt.stock[j])) for k, f in STALL_SIZES.items()}
                     for j in best}
    return dict(
        title=e["name"], start=e["start"].strftime("%Y-%m-%d %H:%M"),
        end=e["end"].round("min").strftime("%Y-%m-%d %H:%M"), indoor=int(e["indoor"]),
        description=str(e.get("description", ""))[:400], cost=round(float(e["cost"]), 2),
        product_ids={bid: p["product_id"] for bid, p in prod.items()},
        product_reviews={opt.bids[j]: round(float(res["signups"] * opt.r[i, j]), 1) for j in best},
        product_matches={opt.bids[j]: round(float(parts["match"][i, j]), 3) for j in best},
        archetype_winner=winner,
        checks=dict(vegan=bool((lb["vegan"] == 1).any()), gluten_free=bool((lb["gluten_free"] == 1).any()),
                    chilled_ok=bool((lb["needs_chilling"] == 1).sum() <= MAX_CHILLED),
                    alcohol_ok=bool(not (restricted and (lb["adults_only"] == 1).any())),
                    in_stock=bool(all(opt.units[i, j] <= opt.stock[j] for j in best))),
        adults_restricted=restricted,
        units_by_size=units_by_size,
        size_line=f"{len(best)} products for about {int(e['footfall'])} people")


def event_audience(events, parts):
    """Crowd archetype mix per event, for the 'Who is attending' panel and archetype chips."""
    out = {}
    for i, e in enumerate(events.itertuples()):
        mix = parts["mix"][i]
        order = np.argsort(-mix)
        out[e.event_id] = dict(crowd={a: round(float(v), 4) for a, v in zip(ARCHETYPES, mix)},
                               top_archetypes=[ARCHETYPES[k] for k in order[:3]],
                               source_note="estimated crowd mix: the event's keyword archetype scores, blended "
                                           "with the WatchHumans population")
    return out


def money(opt, i, lineup, res, cost, A):
    """Pound value of a lineup at event i, and the chance it loses money."""
    units = int(opt.units[i, list(lineup)].sum())
    v = value(res["signups"], res["reviews"], units, float(cost), A)
    rps = res["reviews"] / res["signups"] if res["signups"] else 0
    return {**rounded(v), "units_total": units, "p_waste": round(p_waste(res["signups"], rps, units, float(cost), A), 3)}


def check(d, events, scores, lineups, profs, impact, A):
    b = d["brands"]
    assert len(scores) == len(events) * len(b)
    for eid, l in lineups.items():
        lb = b.loc[l["brands"]]
        assert len(set(l["brands"])) == l["lineup_size"] and 2 <= l["lineup_size"] <= 5, eid
        assert (lb["vegan"] == 1).any() and (lb["gluten_free"] == 1).any() and (lb["needs_chilling"] == 1).sum() <= 2, eid
    assert len(profs) == len(b) and all(len(p["fit_by_type"]) == len(d["event_types"]) for p in profs.values())
    assert impact["review_ci_low"] <= impact["review_uplift"] <= impact["review_ci_high"]
    assert (events["footfall"] < A["max_attendance"]).all()


if __name__ == "__main__":
    main()
