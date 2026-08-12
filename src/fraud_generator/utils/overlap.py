"""Two-class sampling with deliberate overlap.

Most enrichers used to pick a field with a branch like::

    if is_fraud:
        tx["device_age_days"] = randint(0, 90)     # fraud = new device
    else:
        tx["device_age_days"] = randint(30, 730)   # legit = established

Those two ranges barely touch, so ``device_age_days < 30`` identifies fraud with
100.0000% precision. A model trained on that learns a lookup table, and the
lookup table does not exist in production. Measured on a 268k batch, four such
comparisons captured 93.78% of all fraud with zero false positives.

The fix is not "weaker signal" — scaling the gap down still leaves a threshold
that separates. The fix is **contamination in both directions**:

* a share of frauds must look completely ordinary (a mule account bought years
  ago; a fraudster on a three-year-old phone), and
* a share of legitimate records must carry the suspicious value (someone who
  opened a digital account this morning and received a PIX; a MEI registered
  last week).

Both populations are real. Once each class draws from the other's region, no
single threshold reaches high precision, and the classifier has to combine
weak evidence — which is what fraud detection actually is.

Usage::

    from ..utils.overlap import two_class

    tx["device_age_days"] = two_class(
        is_fraud,
        legit=lambda: _lognormal_days(median=220, sigma=1.1, hi=1825),
        fraud=lambda: _lognormal_days(median=55, sigma=1.0, hi=1825),
        rng=rng,
    )

Tune the two contamination rates per field from domain knowledge, not from a
target AUC. The acceptance criterion is in `tests/unit/test_no_perfect_separator.py`:
no single threshold on any numeric field may exceed ~40% precision at the
configured fraud rate.
"""

from __future__ import annotations

import math
import random as _random_module
from typing import Callable, Optional, TypeVar

T = TypeVar("T")

# Share of fraud records that draw from the legitimate distribution instead of
# the suspicious one. Fraud rings buy aged accounts and use ordinary phones.
DEFAULT_FRAUD_CONTAMINATION = 0.30

# Share of legitimate records that draw from the suspicious distribution.
# Brazil opens millions of digital accounts a month, and a brand-new account
# receiving a transfer on day one is completely normal.
DEFAULT_LEGIT_CONTAMINATION = 0.07


def two_class(
    is_fraud: bool,
    *,
    legit: Callable[[], T],
    fraud: Callable[[], T],
    rng: Optional[_random_module.Random] = None,
    fraud_contamination: float = DEFAULT_FRAUD_CONTAMINATION,
    legit_contamination: float = DEFAULT_LEGIT_CONTAMINATION,
) -> T:
    """Draw a value for either class, with each class sampling the other's region.

    Args:
        is_fraud: Which class this record belongs to.
        legit: Zero-arg sampler for the ordinary population.
        fraud: Zero-arg sampler for the suspicious population.
        rng: Random source; falls back to the `random` module.
        fraud_contamination: Probability a fraud record draws from `legit`.
        legit_contamination: Probability a legit record draws from `fraud`.

    Returns:
        A value from one of the two samplers.
    """
    r = rng or _random_module
    if is_fraud:
        return legit() if r.random() < fraud_contamination else fraud()
    return fraud() if r.random() < legit_contamination else legit()


def lognormal_days(
    median: float,
    sigma: float = 1.0,
    lo: float = 0.0,
    hi: float = 3650.0,
    rng: Optional[_random_module.Random] = None,
) -> int:
    """Sample an age in days from a log-normal centred on *median*.

    Ages (of an account, a device, a company) are multiplicative quantities with
    a long right tail — a log-normal fits them far better than the uniform
    ranges this replaces, and it produces no hard edge at the boundary for a
    threshold to latch onto.
    """
    r = rng or _random_module
    value = math.exp(r.gauss(math.log(max(median, 0.5)), sigma))
    return int(max(lo, min(value, hi)))


def truncated_gauss(
    mean: float,
    sd: float,
    lo: float,
    hi: float,
    rng: Optional[_random_module.Random] = None,
) -> float:
    """Sample from a normal distribution clamped to [lo, hi].

    Clamping piles a little mass on the bounds, so keep the bounds well outside
    ±3 sd unless the bound is physically real (a probability cannot exceed 1).
    """
    r = rng or _random_module
    return max(lo, min(r.gauss(mean, sd), hi))


def beta_score(
    alpha: float,
    beta: float,
    rng: Optional[_random_module.Random] = None,
) -> float:
    """Sample a [0, 1] score from a Beta distribution.

    Used for detector-style scores (bot confidence, risk proxies). A Beta with
    a long tail toward the opposite class is what makes a score realistic: a
    sluggish human scores bot-like sometimes, and a good bot scores human-like
    sometimes.
    """
    r = rng or _random_module
    return r.betavariate(alpha, beta)
