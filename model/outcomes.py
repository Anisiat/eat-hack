"""Step 2: expected sign-ups, reviews and qualified reviews (QRP).

Two Poisson regressions trained on the 48 training pop-ups:
  sign-ups per pop-up      ~ log footfall + dwell + lineup archetype match + event type
  reviews per brand / sign-up ~ fit + dwell + event type   (fitted as a rate, weighted by sign-ups)
QRP for brand b = sign-ups x r_b x q_b, where q_b is the crowd share in b's target archetypes.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_poisson_deviance

from .fit import coverage

ALPHA = 1e-3


@dataclass
class OutcomeModel:
    types: list
    signup: PoissonRegressor
    review: PoissonRegressor
    stop_rate: dict             # event_type -> stops per person passing
    test_deviance: float
    baseline_deviance: float

    def _onehot(self, etypes):
        return np.array([[t == k for k in self.types] for t in etypes], float)

    def signups(self, events, appeal):
        """Expected sign-ups; appeal may be (events,) or (events, n_lineups)."""
        appeal = np.asarray(appeal, float)
        base = np.column_stack([np.log(events["footfall"].to_numpy(float)), events["dwell_hours"].to_numpy(float),
                                np.zeros(len(events)), self._onehot(events["event_type"])])
        lin0 = base @ self.signup.coef_ + self.signup.intercept_          # appeal column zeroed
        beta = self.signup.coef_[2]
        if appeal.ndim == 1:
            return np.exp(lin0 + beta * appeal)
        return np.exp(lin0[:, None] + beta * appeal)

    def review_rate(self, events, fit):
        """Reviews per sign-up for each event x brand, capped at 1."""
        n_e, n_b = fit.shape
        X = np.column_stack([fit.ravel(), np.repeat(events["dwell_hours"].to_numpy(float), n_b),
                             np.repeat(self._onehot(events["event_type"]), n_b, axis=0)])
        return np.minimum(self.review.predict(X).reshape(n_e, n_b), 1.0)


def _signup_X(events, appeal, types):
    onehot = np.array([[t == k for k in types] for t in events["event_type"]], float)
    return np.column_stack([np.log(events["footfall"].to_numpy(float)), events["dwell_hours"].to_numpy(float),
                            np.asarray(appeal, float), onehot])


def train(d, past, past_parts):
    """past: past_events(d); past_parts: fit.score(d, fm, past)."""
    types = d["event_types"].index.tolist()
    bids = list(d["brands"].index)
    lineups = past["lineup"].str.split("|")
    appeal = np.array([coverage(past_parts, i, [bids.index(b) for b in lu]) for i, lu in enumerate(lineups)])
    is_train = (past["split"] == "train").to_numpy()

    signup = PoissonRegressor(alpha=ALPHA, max_iter=3000)
    signup.fit(_signup_X(past[is_train], appeal[is_train], types), past.loc[is_train, "signups"])

    # review rate per brand at each training pop-up
    pb = d["popup_brands"].merge(past[["popup_id", "signups", "dwell_hours", "event_type", "split"]], on="popup_id")
    pb = pb[(pb["split"] == "train") & (pb["signups"] > 0)]
    row = past.index.get_indexer(pb["popup_id"])
    col = [bids.index(b) for b in pb["brand_id"]]
    onehot = np.array([[t == k for k in types] for t in pb["event_type"]], float)
    X = np.column_stack([past_parts["fit"][row, col], pb["dwell_hours"].to_numpy(float), onehot])
    review = PoissonRegressor(alpha=ALPHA, max_iter=3000)
    review.fit(X, pb["reviews"] / pb["signups"], sample_weight=pb["signups"])

    tr = past[is_train]
    overall = tr["stops"].sum() / tr["footfall"].sum()
    by_type = tr.groupby("event_type")[["stops", "footfall"]].sum()
    stop_rate = {t: float(by_type.at[t, "stops"] / by_type.at[t, "footfall"]) if t in by_type.index else overall
                 for t in types}

    # held-out check: Poisson model against footfall x average sign-up rate
    te = past[~is_train]
    pred = signup.predict(_signup_X(te, appeal[~is_train], types))
    base = te["footfall"] * tr["signups"].sum() / tr["footfall"].sum()
    return OutcomeModel(types, signup, review, stop_rate,
                        float(mean_poisson_deviance(te["signups"], pred)),
                        float(mean_poisson_deviance(te["signups"], base)))


def brand_outcomes(om, events, parts, signups):
    """Per event x brand expected reviews and QRP, given expected sign-ups per event."""
    r = om.review_rate(events, parts["fit"])
    reviews = signups[:, None] * r
    return r, reviews, reviews * parts["q"]
