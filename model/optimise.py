"""Steps 3 and 6: best 5-brand lineup per event, units to bring and the time slot.

Every 5-brand combination of the 20 brands (15,504) is scored at once with numpy.
Score = expected QRP x 1.10 if drink, savoury, sweet and condiment are all covered
        x 0.85 per pair of brands sharing a sub-category.
Hard constraints: >= 1 vegan, >= 1 gluten-free, <= 2 chilled brands, frozen only indoors, units in stock.
"""
from itertools import combinations

import numpy as np
import pandas as pd

from .data import CORE_CATEGORIES, nice

LINEUP_SIZE = 5
COVER_BONUS = 1.10
SAME_SUB_PENALTY = 0.85
MAX_CHILLED = 2
UNIT_BUFFER = 1.2


class Optimiser:
    def __init__(self, d, om, events, parts):
        self.d, self.om, self.events, self.parts = d, om, events, parts
        b = d["brands"]
        self.bids = list(b.index)
        self.combos = np.array(list(combinations(range(len(b)), LINEUP_SIZE)))
        C = self.combos
        cat = b["category"].to_numpy()
        sub = b["sub_category"].to_numpy()
        covered = np.ones(len(C), bool)
        for k in CORE_CATEGORIES:
            covered &= (cat[C] == k).any(1)
        same_sub = sum((sub[C[:, x]] == sub[C[:, y]]) for x, y in combinations(range(LINEUP_SIZE), 2))
        self.shape = np.where(covered, COVER_BONUS, 1.0) * SAME_SUB_PENALTY ** same_sub
        self.base_ok = ((b["vegan"].to_numpy()[C] == 1).any(1) & (b["gluten_free"].to_numpy()[C] == 1).any(1)
                        & ((b["needs_chilling"].to_numpy()[C] == 1).sum(1) <= MAX_CHILLED))
        self.has_frozen = (b["frozen"].to_numpy()[C] == 1).any(1)
        self.stock = b["units_available_per_month"].to_numpy()
        self.habit = [self.bids.index(x) for x in b.index[b["favourite_five"] == 1]]

        self.r = om.review_rate(events, parts["fit"])
        self.rq = self.r * parts["q"]
        self.stops = np.array([e.footfall * om.stop_rate[e.event_type] for e in events.itertuples()])
        self.units = np.minimum(np.ceil(self.stops[:, None] * UNIT_BUFFER), self.stock[None, :]).astype(int)

    def evaluate(self, i, lineup):
        """Expected outcomes of one lineup (brand indices) at event i."""
        lineup = list(lineup)
        appeal = self.parts["fit"][i, lineup].mean()
        s = float(self.om.signups(self.events.iloc[[i]], [appeal])[0])
        per_brand = s * self.rq[i, lineup]
        reviews = s * self.r[i, lineup]
        return dict(signups=s, qrp=float(per_brand.sum()), reviews=float(reviews.sum()),
                    per_brand=dict(zip([self.bids[j] for j in lineup], per_brand)))

    def feasible(self, i, lineup):
        b = self.d["brands"].iloc[list(lineup)]
        ok = (b["vegan"] == 1).any() and (b["gluten_free"] == 1).any() and (b["needs_chilling"] == 1).sum() <= MAX_CHILLED
        if self.events["indoor"].iloc[i] == 0:
            ok &= not (b["frozen"] == 1).any()
        need = np.ceil(self.stops[i] * UNIT_BUFFER)
        return bool(ok and (self.stock[list(lineup)] >= min(need, self.stock.min())).all())

    def best(self, i):
        """Best lineup at event i: (brand indices, objective)."""
        C = self.combos
        fit = self.parts["fit"][i]
        appeal = fit[C].mean(1)
        s = self.om.signups(self.events.iloc[[i]], appeal[None, :])[0]
        qrp = s * self.rq[i][C].sum(1)
        ok = self.base_ok.copy()
        if self.events["indoor"].iloc[i] == 0:
            ok &= ~self.has_frozen
        need = np.ceil(self.stops[i] * UNIT_BUFFER)
        in_stock = self.stock >= min(need, self.stock.min())
        ok &= in_stock[C].all(1)
        obj = np.where(ok, qrp * self.shape, -np.inf)
        k = int(np.argmax(obj))
        return list(C[k]), float(obj[k])

    def slot(self, i):
        """Peak-need window from the crowd table, clipped to the event's own hours."""
        e = self.events.iloc[i]
        peak = self.d["event_types"].at[e["event_type"], "peak_slot"]
        start, end = pd.Timestamp(e["start"]), pd.Timestamp(e["end"])
        if peak == "interval":
            mid = start + (end - start) / 2
            return f"{(mid - pd.Timedelta(minutes=10)):%H:%M}-{(mid + pd.Timedelta(minutes=15)):%H:%M} (interval)"
        if peak == "finish":
            return f"{(end - pd.Timedelta(minutes=30)):%H:%M}-{(end + pd.Timedelta(minutes=30)):%H:%M} (finish)"
        lo, hi = peak.split("-")
        lo_t = pd.Timestamp(f"{start.date()} {lo}")
        hi_t = pd.Timestamp(f"{start.date()} {hi}")
        if lo_t < start or hi_t > end:      # window outside the event: use its middle two hours
            mid = start + (end - start) / 2
            lo_t, hi_t = max(start, mid - pd.Timedelta(hours=1)), min(end, mid + pd.Timedelta(hours=1))
        return f"{lo_t:%H:%M}-{hi_t:%H:%M}"


def lineup_reasons(d, opt, i, lineup, res, habit_res, brand_reason):
    b = d["brands"].iloc[lineup]
    vs = res["qrp"] / habit_res["qrp"] - 1 if habit_res["qrp"] else 0
    top = max(lineup, key=lambda j: res["per_brand"][opt.bids[j]])
    cats = sorted(set(b["category"]))
    return [f"Expected {res['qrp']:.0f} qualified reviews against {habit_res['qrp']:.0f} for the usual five "
            f"({vs:+.0%})",
            f"{d['brands'].iloc[top]['brand_name']}: {brand_reason(i, top)[0]}",
            f"Covers {', '.join(nice(c) for c in cats)}; {int(b['vegan'].sum())} vegan and "
            f"{int(b['gluten_free'].sum())} gluten-free options"]
