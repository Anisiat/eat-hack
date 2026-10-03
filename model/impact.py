"""Impact test on the 12 held-out pop-ups, in reviews and in pounds.

For each test pop-up the trained model picks a lineup (sized to the crowd). The tool lineup and RGC's usual
lineup of the same size are then played out in the generator's hidden world (simulate, expected values), and
both are valued with data/assumptions/value_assumptions.csv. This is the only module that touches the generator, and only
to judge, never to choose.
"""
import sys

import numpy as np

from .data import ROOT
from .value import time_saved, value

sys.path.insert(0, str(ROOT / "scripts"))
from generate_popups import simulate  # noqa: E402

N_BOOT = 2000
SEED = 42


def uplift_test(d, opt_test, test, A):
    """opt_test: Optimiser over the test pop-ups (past_events rows with split == 'test')."""
    rows, tr, hr, tn, hn = [], [], [], [], []
    for i in range(len(test)):
        e = test.iloc[i]
        lineup, _ = opt_test.best(i)
        habit_idx = opt_test.habit_for(i)
        world = dict(event_type=e["event_type"], footfall=int(e["footfall"]), indoor=int(e["indoor"]),
                     temp_c=float(e["temp_c"]))
        out = {}
        for name, idx in (("tool", lineup), ("habit", habit_idx)):
            sim = simulate(world, [opt_test.bids[j] for j in idx])
            units = int(opt_test.units[i, list(idx)].sum())
            out[name] = dict(signups=sim["signups"], reviews=sim["reviews"],
                             **value(sim["signups"], sim["reviews"], units, float(e["cost"]), A))
        tr.append(out["tool"]["reviews"])
        hr.append(out["habit"]["reviews"])
        tn.append(out["tool"]["net_value"])
        hn.append(out["habit"]["net_value"])
        rows.append(dict(popup_id=e["popup_id"], event_type=e["event_type"], footfall=int(e["footfall"]),
                         lineup_size=len(lineup), tool_lineup=[opt_test.bids[j] for j in lineup],
                         reviews_tool=round(out["tool"]["reviews"], 1), reviews_habit=round(out["habit"]["reviews"], 1),
                         net_value_tool=round(out["tool"]["net_value"], 2),
                         net_value_habit=round(out["habit"]["net_value"], 2)))
    tr, hr, tn, hn = map(np.array, (tr, hr, tn, hn))
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(test), (N_BOOT, len(test)))
    boot_r = tr[idx].sum(1) / hr[idx].sum(1) - 1
    boot_n = (tn - hn)[idx].mean(1)
    gain = float((tn - hn).mean())
    t = time_saved(A)
    per_month = A["popups_per_month"]
    return dict(
        review_uplift=round(float(tr.sum() / hr.sum() - 1), 4),
        review_ci_low=round(float(np.percentile(boot_r, 2.5)), 4),
        review_ci_high=round(float(np.percentile(boot_r, 97.5)), 4),
        reviews_tool=round(float(tr.mean()), 2), reviews_habit=round(float(hr.mean()), 2),
        net_value_tool=round(float(tn.mean()), 2), net_value_habit=round(float(hn.mean()), 2),
        net_gain_per_popup=round(gain, 2),
        net_gain_ci_low=round(float(np.percentile(boot_n, 2.5)), 2),
        net_gain_ci_high=round(float(np.percentile(boot_n, 97.5)), 2),
        waste_rate_tool=round(float((tn < 0).mean()), 3), waste_rate_habit=round(float((hn < 0).mean()), 3),
        monthly_lineup_gain_gbp=round(gain * per_month, 2),
        monthly_hours_saved=round(t["hours_per_month"], 1),
        monthly_time_saved_gbp=round(t["gbp_per_month"], 2),
        monthly_impact_gbp=round(gain * per_month + t["gbp_per_month"], 2),
        yearly_impact_gbp=round(12 * (gain * per_month + t["gbp_per_month"]), 2),
        n_test=len(test),
        method="tool vs usual lineup (same size) at the same 12 held-out pop-ups; outcomes from the synthetic "
               "world, valued with data/assumptions/value_assumptions.csv; 95% bootstrap CIs",
        per_popup=rows)
