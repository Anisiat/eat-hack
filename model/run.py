"""Run the Pop-up Pick model end to end and write outputs/.

  python -m model.run [--month 2026-11] [--capacity 2]

Writes outputs/scores.csv, lineups.json, profiles.json, impact.json, month_plan.json
and 5-row stubs of each in outputs/stubs/.
"""
import argparse
import json

import numpy as np
import pandas as pd

from . import fit as fitmod
from . import outcomes, plan, profiles
from .data import OUT, load, past_events, upcoming_events
from .impact import uplift_test
from .optimise import Optimiser, lineup_reasons


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
    ap.add_argument("--month", default="2026-11")
    ap.add_argument("--capacity", type=int, default=2)   # RGC runs 2 pop-ups a month
    args = ap.parse_args()

    d = load()
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
        habit = opt.evaluate(i, opt.habit)
        lineups[e.event_id] = dict(
            name=e.name, date=e.date, event_type=e.event_type, borough=e.borough,
            brands=[opt.bids[j] for j in best],
            units={opt.bids[j]: int(opt.units[i, j]) for j in best},
            slot=opt.slot(i), exp_signups=round(res["signups"], 1), exp_reviews=round(res["reviews"], 1),
            qrp=round(res["qrp"], 1), habit_brands=[opt.bids[j] for j in opt.habit],
            habit_qrp=round(habit["qrp"], 1), cost=round(float(e.cost), 2),
            cost_per_qr=round(e.cost / res["qrp"], 2) if res["qrp"] else None,
            habit_cost_per_qr=round(e.cost / habit["qrp"], 2) if habit["qrp"] else None,
            reasons=lineup_reasons(d, opt, i, best, res, habit, brand_reason))
        # brand-level scores in the context of the best lineup's sign-ups
        s = res["signups"]
        for j, bid in enumerate(opt.bids):
            rs = brand_reason(i, j)
            score_rows.append(dict(event_id=e.event_id, brand_id=bid, fit=round(float(parts["fit"][i, j]), 4),
                                   exp_signups=round(s, 1), exp_reviews=round(s * opt.r[i, j], 2),
                                   exp_qrp=round(s * opt.rq[i, j], 2), in_best_lineup=int(j in best),
                                   reason_1=rs[0], reason_2=rs[1], reason_3=rs[2]))
    scores = pd.DataFrame(score_rows)

    # 4. month plan
    month = plan.month_plan(d, opt, events, lineups, args.month, args.capacity)

    # 5. brand profiles
    profs = profiles.build(d, fm, scores, events)

    # uplift on the 12 held-out pop-ups
    test = past[past["split"] == "test"]
    impact = uplift_test(d, Optimiser(d, om, test, fitmod.score(d, fm, test)), test)
    impact["poisson_test_deviance"] = round(om.test_deviance, 3)
    impact["footfall_baseline_test_deviance"] = round(om.baseline_deviance, 3)

    check(d, events, scores, lineups, profs, impact)

    OUT.mkdir(exist_ok=True)
    (OUT / "stubs").mkdir(exist_ok=True)
    scores.to_csv(OUT / "scores.csv", index=False)
    to_json(lineups, OUT / "lineups.json")
    to_json(profs, OUT / "profiles.json")
    to_json(impact, OUT / "impact.json")
    to_json(month, OUT / "month_plan.json")
    scores.head(5).to_csv(OUT / "stubs" / "scores.csv", index=False)
    to_json(dict(list(lineups.items())[:5]), OUT / "stubs" / "lineups.json")
    to_json(dict(list(profs.items())[:5]), OUT / "stubs" / "profiles.json")
    to_json({k: v for k, v in impact.items() if k != "per_popup"}, OUT / "stubs" / "impact.json")
    to_json({**month, "popups": month["popups"][:2]}, OUT / "stubs" / "month_plan.json")

    lq = np.mean([v["qrp"] for v in lineups.values()])
    hq = np.mean([v["habit_qrp"] for v in lineups.values()])
    print(f"{len(events)} events x {len(opt.bids)} brands scored. Mean QRP per event: tool {lq:.1f}, habit {hq:.1f}")
    print(f"Held-out uplift: {impact['uplift']:+.1%} (95% CI {impact['ci_low']:+.1%} to {impact['ci_high']:+.1%}); "
          f"cost per qualified review £{impact['cost_per_qr_tool']} vs £{impact['cost_per_qr_habit']}")
    print(f"Sign-up model test deviance {om.test_deviance:.2f} vs footfall baseline {om.baseline_deviance:.2f}")
    print(f"Month plan {month['month']}: {len(month['popups'])} pop-ups, QRP {month['total_qrp']} vs habit "
          f"{month['habit_total_qrp']}, {month['brands_featured']}/20 brands featured")
    print(f"Wrote outputs to {OUT}/")


def check(d, events, scores, lineups, profs, impact):
    b = d["brands"]
    assert len(scores) == len(events) * len(b)
    for eid, l in lineups.items():
        lb = b.loc[l["brands"]]
        assert len(set(l["brands"])) == 5, eid
        assert (lb["vegan"] == 1).any() and (lb["gluten_free"] == 1).any() and (lb["needs_chilling"] == 1).sum() <= 2, eid
    assert len(profs) == len(b) and all(len(p["fit_by_type"]) == len(d["event_types"]) for p in profs.values())
    assert impact["ci_low"] <= impact["uplift"] <= impact["ci_high"]


if __name__ == "__main__":
    main()
