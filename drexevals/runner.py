"""Suite runner: accuracy + confidence calibration (ECE-style bins)."""

from __future__ import annotations

from .types import Answer, DecisionRequest


def run_suite(client, cases: list[dict]) -> dict:
    """cases: [{state: {...}, questions: [...], expected: {qname: option}}].

    Returns per-question accuracy, avg confidence on correct/incorrect, and
    5-bin expected-vs-observed calibration for every scored question.
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
            stats = per_q.setdefault(qname, {
                "n": 0, "correct": 0, "conf_sum": 0.0,
                "conf_correct": 0.0, "conf_wrong": 0.0,
                "bins": [[] for _ in range(5)],
            })
            conf = max(probs.values()) if probs else 0.0
            stats["n"] += 1
            stats["conf_sum"] += conf
            if chosen == expected:
                stats["correct"] += 1
                stats["conf_correct"] += conf
            else:
                stats["conf_wrong"] += conf
            bin_idx = min(int(conf * 5), 4)
            stats["bins"][bin_idx].append(1.0 if chosen == expected else 0.0)

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
        report[qname] = {
            "n": s["n"],
            "accuracy": s["correct"] / s["n"],
            "avg_confidence": s["conf_sum"] / s["n"],
            "confidence_on_correct": s["conf_correct"] / max(s["correct"], 1),
            "confidence_on_wrong": s["conf_wrong"] / max(s["n"] - s["correct"], 1),
            "calibration_bins": bins,
        }
    return report
