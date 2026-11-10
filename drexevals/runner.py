"""Suite runner: accuracy + calibration (Brier score, ECE, reliability bins)."""

from __future__ import annotations

from .types import Answer, DecisionRequest

N_ECE_BINS = 10


def run_suite(client, cases: list[dict]) -> dict:
    """cases: [{state: {...}, questions: [...], expected: {qname: option}}].

    Returns per-question accuracy, avg confidence on correct/incorrect,
    5-bin reliability data, the multi-class Brier score and the 10-bin
    expected calibration error (ECE) for every scored question.

    Definitions (confidence = probability of the chosen option):
    - brier: mean over cases of sum over returned options
      (p_option - 1[option == expected])^2, plus (0 - 1)^2 when the expected
      label is absent from the options (label-union form — omitting the right
      answer is penalized, not rewarded). 0 is perfect, lower is better.
    - ece: sum over 10 equal-width confidence bins of
      (n_bin / n) * |observed accuracy - avg confidence| in the bin.
      0 is perfectly calibrated.

    Questions without an expected label are skipped, not counted as wrong.
    """
    per_q: dict[str, dict] = {}
    for case in cases:
        request = DecisionRequest(
            state=case["state"],
            questions=case["questions"],
        )
        answer: Answer = client.decide(request)
        for qname, (chosen, probs) in answer.per_question.items():
            expected = case["expected"].get(qname)
            if expected is None:
                continue
            stats = per_q.setdefault(qname, {
                "n": 0, "correct": 0, "conf_sum": 0.0,
                "conf_correct": 0.0, "conf_wrong": 0.0, "brier_sum": 0.0,
                "bins": [[] for _ in range(5)],
                "ece_bins": [[] for _ in range(N_ECE_BINS)],
            })
            conf = max(probs.values()) if probs else 0.0
            correct = chosen == expected
            stats["n"] += 1
            stats["conf_sum"] += conf
            brier = sum(
                (p - (1.0 if opt == expected else 0.0)) ** 2
                for opt, p in probs.items()
            )
            if expected not in probs:
                brier += 1.0  # expected class absent: (0 - 1)^2 over the label union
            stats["brier_sum"] += brier
            if correct:
                stats["correct"] += 1
                stats["conf_correct"] += conf
            else:
                stats["conf_wrong"] += conf
            bin_idx = min(max(int(conf * 5), 0), 4)  # clamp: bad endpoints may emit p < 0
            stats["bins"][bin_idx].append(1.0 if correct else 0.0)
            ece_idx = min(max(int(conf * N_ECE_BINS), 0), N_ECE_BINS - 1)
            stats["ece_bins"][ece_idx].append((conf, 1.0 if correct else 0.0))

    report = {}
    for qname, s in per_q.items():
        bins = []
        for i, b in enumerate(s["bins"]):
            if b:
                bins.append({
                    "confidence_range": f"{i / 5:.1f}-{(i + 1) / 5:.1f}",
                    "n": len(b),
                    "observed_accuracy": sum(b) / len(b),
                })
        ece = 0.0
        ece_bins = []
        for i, b in enumerate(s["ece_bins"]):
            if not b:
                continue
            conf_b = sum(c for c, _ in b) / len(b)
            acc_b = sum(r for _, r in b) / len(b)
            ece += (len(b) / s["n"]) * abs(acc_b - conf_b)
            ece_bins.append({
                "confidence_range": f"{i / N_ECE_BINS:.1f}-{(i + 1) / N_ECE_BINS:.1f}",
                "n": len(b),
                "avg_confidence": conf_b,
                "observed_accuracy": acc_b,
            })
        report[qname] = {
            "n": s["n"],
            "accuracy": s["correct"] / s["n"],
            "avg_confidence": s["conf_sum"] / s["n"],
            "confidence_on_correct": s["conf_correct"] / max(s["correct"], 1),
            "confidence_on_wrong": s["conf_wrong"] / max(s["n"] - s["correct"], 1),
            "calibration_bins": bins,
            "brier": s["brier_sum"] / s["n"],
            "ece": ece,
            "ece_bins": ece_bins,
        }
    return report
