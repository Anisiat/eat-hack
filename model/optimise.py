"""Steps 3 and 6: best 5-brand lineup per event, units to bring and the time slot.

Lineup size scales with expected attendance: 2 products under 50 people, 3 under 100, 4 under 150, else 5
(events are capped below 200 people).
Each event shortlists its 20 best eligible brands on their own match, then every combination of that size
(up to 15,504 for 5) is scored at once with numpy.
Score = archetype match of the lineup to the event's expected crowd (fit.coverage): every expected archetype
is credited with its favourite product in the lineup, so five products that each win a different part of the
crowd beat five near-duplicates. Expected sign-ups, reviews and pound value are forecast for the chosen lineup.
Hard constraints: >= 1 vegan, >= 1 gluten-free, <= 2 chilled brands, frozen only indoors, units in stock,
no adults-only brands (alcohol, CBD) at community, expo or conference events.
"""
from itertools import combinations

import numpy as np
import pandas as pd

from .data import ARCHETYPES as ARCH, nice
from .fit import coverage

# products to bring scale with expected attendance: (attendance below, lineup size)
SIZE_TIERS = [(50, 2), (100, 3), (150, 4), (float("inf"), 5)]     # events are capped below 200 people
MAX_SIZE = 5
MAX_CHILLED = 2
UNIT_BUFFER = 1.2
SHORTLIST = 20
NO_ADULTS = {"community", "expos", "conferences"}


class Optimiser:
    def __init__(self, d, om, events, parts):
        self.d, self.om, self.events, self.parts = d, om, events, parts
        b = d["brands"]
        self.bids = list(b.index)
        self.cat = b["category"].to_numpy()
        self.sub = b["sub_category"].to_numpy()
        self.vegan = b["vegan"].to_numpy() == 1
        self.gf = b["gluten_free"].to_numpy() == 1
        self.chill = b["needs_chilling"].to_numpy() == 1
        self.frozen = b["frozen"].to_numpy() == 1
        self.adults = b["adults_only"].to_numpy() == 1
        self.stock = b["units_available_per_month"].to_numpy()
        fav = b[b["favourite_five"] == 1].sort_values(["n_products", "brand_name"], ascending=[False, True])
        self.habit = [self.bids.index(x) for x in fav.index]          # usual five, biggest shelf presence first
        self.positions = {k: np.array(list(combinations(range(SHORTLIST), k))) for _, k in SIZE_TIERS}

        self.r = om.review_rate(events, parts["fit"])
        self.stops = np.array([e.footfall * om.stop_rate[e.event_type] for e in events.itertuples()])
        self.units = np.minimum(np.ceil(self.stops[:, None] * UNIT_BUFFER), self.stock[None, :]).astype(int)

    def size(self, i):
        """How many products to bring: 2 under 50 attendees, 3 under 100, 4 under 150, else 5."""
        att = self.events["footfall"].iloc[i]
        return next(k for limit, k in SIZE_TIERS if att < limit)

    def habit_for(self, i):
        """RGC's usual lineup at the same size: the first k of the usual five."""
        return self.habit[:self.size(i)]

    def eligible(self, i):
        """Brands allowed at event i on their own (setting, audience and stock rules)."""
        ok = np.ones(len(self.bids), bool)
        if self.events["indoor"].iloc[i] == 0:
            ok &= ~self.frozen
        if self.events["event_type"].iloc[i] in NO_ADULTS:
            ok &= ~self.adults
        need = np.ceil(self.stops[i] * UNIT_BUFFER)
        return ok & (self.stock >= min(need, self.stock.min()))

    def evaluate(self, i, lineup):
        """Archetype match and expected outcomes of one lineup (brand indices) at event i."""
        lineup = list(lineup)
        match = coverage(self.parts, i, lineup)
        s = float(self.om.signups(self.events.iloc[[i]], [match])[0])
        reviews = s * self.r[i, lineup]
        return dict(match=match, signups=s, reviews=float(reviews.sum()),
                    per_brand=dict(zip([self.bids[j] for j in lineup], reviews)))

    def feasible(self, i, lineup):
        L = list(lineup)
        return bool(self.eligible(i)[L].all() and self.vegan[L].any() and self.gf[L].any()
                    and self.chill[L].sum() <= MAX_CHILLED)

    def best(self, i):
        """Best lineup at event i: (brand indices, objective)."""
        ok = self.eligible(i)
        cand = np.flatnonzero(ok)
        cand = cand[np.argsort(-self.parts["fit"][i, cand])][:SHORTLIST]
        k = self.size(i)
        assert len(cand) >= k, f"fewer than {k} eligible brands at event {i}"
        P = self.positions[k]
        C = cand[P[np.all(P < len(cand), axis=1)]]
        valid = self.vegan[C].any(1) & self.gf[C].any(1) & (self.chill[C].sum(1) <= MAX_CHILLED)
        match = self.parts["per_arch"][i][C].max(1) @ self.parts["mix"][i]      # lineups x archetypes -> lineups
        obj = np.where(valid, match, -np.inf)
        k = int(np.argmax(obj))
        assert np.isfinite(obj[k]), f"no feasible lineup at event {i}"
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
    vs = res["reviews"] / habit_res["reviews"] - 1 if habit_res["reviews"] else 0
    mix = opt.parts["mix"][i]
    fav = opt.parts["per_arch"][i, lineup].argmax(0)                 # each archetype's favourite in the lineup
    big = np.argsort(-mix)[:3]
    who = "; ".join(f"{nice(d['brands'].iloc[lineup[fav[a]]]['brand_name'])} for {nice(ARCH[a])}s" for a in big)
    return [f"Archetype match {res['match']:.2f} against {habit_res['match']:.2f} for the usual lineup: {who}",
            f"Expected {res['reviews']:.0f} reviews and {res['signups']:.0f} sign-ups, against "
            f"{habit_res['reviews']:.0f} reviews for the usual lineup ({vs:+.0%})",
            f"{int(b['vegan'].sum())} vegan and {int(b['gluten_free'].sum())} gluten-free options; "
            f"covers {', '.join(nice(c) for c in sorted(set(b['category'])))}"]
