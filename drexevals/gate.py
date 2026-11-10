"""Act/ask gate over Drex confidences, with empirical risk calibration.

The roadmap question this answers: given the model's calibrated probability,
when can a pipeline auto-act and when must it escalate to a human? Drex is
the System 1 read; this module is the approval layer's decision rule.
"""

from __future__ import annotations

ASK_ALWAYS = 1.1  # above any possible confidence: every decision escalates


def gate(confidence: float, tau: float) -> str:
    """'act' when confidence >= tau, else 'ask' (escalate to a human)."""
    return "act" if confidence >= tau else "ask"


def risk_at(pairs, tau: float) -> tuple[float, float]:
    """(empirical risk, coverage) of auto-acting at threshold tau.

    pairs: iterable of (confidence, correct) — measured decisions.
    Risk is the share of wrong answers among auto-acted; coverage the share
    of decisions auto-acted.
    """
    pairs = list(pairs)
    acted = [(c, ok) for c, ok in pairs if c >= tau]
    if not acted:
        return 0.0, 0.0
    wrong = sum(1 for _, ok in acted if not ok)
    return wrong / len(acted), len(acted) / len(pairs)


def calibrate_threshold(pairs, max_risk: float) -> tuple[float, float, float]:
    """Smallest threshold whose empirical risk stays <= max_risk.

    Returns (tau, coverage, risk); tau = ASK_ALWAYS when no threshold holds
    (escalate everything).

    ponytail: empirical risk on the calibration pairs, no distribution-free
    guarantee — for a conformal-style bound, calibrate on a held-out split
    and pay the sample-size correction (methodology: gate-calibrated repo).
    """
    pairs = list(pairs)
    for tau in sorted({c for c, _ in pairs}):
        risk, coverage = risk_at(pairs, tau)
        if risk <= max_risk:
            return tau, coverage, risk
    return ASK_ALWAYS, 0.0, 0.0
