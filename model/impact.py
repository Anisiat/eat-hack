"""Uplift test on the 12 held-out pop-ups.

For each test pop-up the trained model picks a lineup. The tool lineup and RGC's usual five are then
scored by the generator's hidden world (simulate, expected values). This is the only module that
touches the generator, and only to judge, never to choose.
"""
import sys

import numpy as np

from .data import ROOT

sys.path.insert(0, str(ROOT / "scripts"))
from generate_popups import simulate  # noqa: E402

N_BOOT = 2000
SEED = 42


def uplift_test(d, opt_test, test):
    """opt_test: Optimiser over the test pop-ups (past_events rows with split == 'test')."""
    tool_q, habit_q, cost, rows = [], [], [], []
    for i in range(len(test)):
        e = test.iloc[i]
        lineup, _ = opt_test.best(i)
        tool = [opt_test.bids[j] for j in lineup]
        habit = [opt_test.bids[j] for j in opt_test.habit]
        world = dict(event_type=e["event_type"], footfall=int(e["footfall"]), indoor=int(e["indoor"]),
                     temp_c=float(e["temp_c"]))
        t = simulate(world, tool)["qualified_reviews"]
        h = simulate(world, habit)["qualified_reviews"]
        tool_q.append(t)
        habit_q.append(h)
        cost.append(float(e["cost"]))
        rows.append(dict(popup_id=e["popup_id"], event_type=e["event_type"], tool_lineup=tool,
                         qrp_tool=round(t, 1), qrp_habit=round(h, 1)))
    tool_q, habit_q, cost = map(np.array, (tool_q, habit_q, cost))
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(test), (N_BOOT, len(test)))
    boot = tool_q[idx].sum(1) / habit_q[idx].sum(1) - 1
    uplift = tool_q.sum() / habit_q.sum() - 1
    return dict(uplift=round(float(uplift), 4),
                ci_low=round(float(np.percentile(boot, 2.5)), 4),
                ci_high=round(float(np.percentile(boot, 97.5)), 4),
                qrp_tool=round(float(tool_q.mean()), 2), qrp_habit=round(float(habit_q.mean()), 2),
                cost_per_qr_tool=round(float(cost.sum() / tool_q.sum()), 2),
                cost_per_qr_habit=round(float(cost.sum() / habit_q.sum()), 2),
                n_test=len(test), method="tool vs habit lineup at the same 12 held-out pop-ups; "
                                         "outcomes from the synthetic world, 95% bootstrap CI",
                per_popup=rows)
