"""What a pop-up is worth in pounds, from things RGC can count with a QR code per pop-up.

net value = sign-ups x value per sign-up          (£0 today: no paid acquisition)
          + reviews x value per review               (£599 / 15 = £39.93, RGC's price to clients)
          + publicity (review videos x views x value per 1,000 views)   (£0 today; views reported for the pitch)
          - event cost (pitch, insurance, consumables, transport, staff food) - product given (units x unit cost)

A pop-up is wasted when its net value comes out below zero. Assumptions live in
data/assumptions/value_assumptions.csv so RGC can replace them with real figures.
"""
import numpy as np
from scipy.stats import poisson

from .data import load_assumptions  # noqa: F401  (re-exported for run.py)


def publicity_per_review(A):
    return A["video_review_share"] * A["views_per_video"] / 1000 * A["value_per_1000_views_gbp"]


def value(signups, reviews, units, cost, A):
    """Pound value of one pop-up's outcomes."""
    publicity = reviews * publicity_per_review(A)
    gross = signups * A["value_per_signup_gbp"] + reviews * A["value_per_review_gbp"] + publicity
    product = units * A["unit_cost_gbp"]
    views = reviews * A["video_review_share"] * A["views_per_video"]       # reach, for the pitch
    return dict(signup_value=signups * A["value_per_signup_gbp"], review_value=reviews * A["value_per_review_gbp"],
                publicity_value=publicity, est_video_views=views, product_cost=product, event_cost=cost,
                net_value=gross - cost - product)


def p_waste(exp_signups, reviews_per_signup, units, cost, A):
    """Chance the pop-up loses money: sign-ups are Poisson, and each brings reviews and publicity with it."""
    per_signup = (A["value_per_signup_gbp"]
                  + reviews_per_signup * (A["value_per_review_gbp"] + publicity_per_review(A)))
    breakeven = (cost + units * A["unit_cost_gbp"]) / max(per_signup, 1e-9)
    return float(poisson.cdf(np.ceil(breakeven) - 1, max(exp_signups, 1e-9)))


def time_saved(A):
    """Marketing time and money saved per month by not choosing events and lineups by hand."""
    hours = (A["marketing_hours_manual"] - A["marketing_hours_tool"]) * A["popups_per_month"]
    return dict(hours_per_month=hours, gbp_per_month=hours * A["marketing_rate_gbp"])


def rounded(d, nd=2):
    return {k: round(float(v), nd) for k, v in d.items()}
