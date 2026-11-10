"""Offline test of the whole eval plumbing (MockDrexClient, zero network)."""

import pytest

from drexevals import MockDrexClient, Question, run_suite

CASES = [
    {
        "state": {"ticket": "I was charged twice, please refund the extra payment"},
        "questions": [
            Question(name="team", type="choice", instructions="Which team?",
                     criteria={"billing": "payments", "technical": "bugs", "other": "rest"}),
            Question(name="refund", type="noul", instructions="Explicit refund request?"),
        ],
        "expected": {"team": "billing", "refund": "noui"},
    },
    {
        "state": {"ticket": "The app crashes on startup since the last update"},
        "questions": [
            Question(name="team", type="choice", instructions="Which team?",
                     criteria={"billing": "payments", "technical": "bugs", "other": "rest"}),
            Question(name="refund", type="noul", instructions="Explicit refund request?"),
        ],
        "expected": {"team": "technical", "refund": "noun"},  # crash ticket: no refund asked
    },
]

# Mock emits only options that appear as rule values, so team probs are
# {billing, technical} (no "other") — probabilities below assume that.
RULES = {
    "team": {"charged": "billing", "refund": "billing", "crashes": "technical", "startup": "technical"},
    "refund": {"refund": "noui"},
}


def test_suite_reports_accuracy_and_calibration():
    report = run_suite(MockDrexClient(RULES), CASES)
    assert report["team"]["accuracy"] == 1.0
    assert report["team"]["n"] == 2
    # calibration bins must exist and be populated
    assert any(b["n"] > 0 for b in report["team"]["calibration_bins"])
    # confident mock: confidence on correct >= confidence on wrong
    assert report["team"]["confidence_on_correct"] >= report["team"]["confidence_on_wrong"]
    # refund: matched in case 1 (conf .9, correct); case 2 single-option fallback
    # (conf .05) picks noui but the ticket asks for no refund -> wrong
    assert report["refund"]["accuracy"] == 0.5
    assert report["refund"]["confidence_on_correct"] == pytest.approx(0.9)
    assert report["refund"]["confidence_on_wrong"] == pytest.approx(0.05)


def test_brier_score():
    report = run_suite(MockDrexClient(RULES), CASES)
    # team, both cases: probs {chosen: .9, other: .05}, expected chosen
    # -> (.1)^2 + (.05)^2 = .0125 each
    assert report["team"]["brier"] == pytest.approx(0.0125)
    # refund: case 1 (1-.9)^2 = .01; case 2 only option noui at .05, expected
    # noun -> (.05)^2 + (0-1)^2 [expected absent from options] = 1.0025;
    # mean = (0.01 + 1.0025) / 2
    assert report["refund"]["brier"] == pytest.approx(0.50625)


def test_ece_ten_bins():
    report = run_suite(MockDrexClient(RULES), CASES)
    # team: both conf .9 in bin [0.9,1.0), all correct -> ece = |1.0 - .9|
    assert report["team"]["ece"] == pytest.approx(0.1)
    team_bins = report["team"]["ece_bins"]
    assert len(team_bins) == 1
    assert team_bins[0]["confidence_range"] == "0.9-1.0"
    assert team_bins[0]["n"] == 2
    assert team_bins[0]["avg_confidence"] == pytest.approx(0.9)
    assert team_bins[0]["observed_accuracy"] == 1.0
    # refund: two bins -> .5*|1-.9| + .5*|0-.05| = .075
    assert report["refund"]["ece"] == pytest.approx(0.075)
    assert [b["confidence_range"] for b in report["refund"]["ece_bins"]] == ["0.0-0.1", "0.9-1.0"]


def test_unlabeled_questions_are_not_scored():
    one = [dict(CASES[0], expected={})]
    assert run_suite(MockDrexClient(RULES), one) == {}


def test_by_group_breakdown_is_additive():
    grouped = [dict(c, group="a" if i == 0 else "b") for i, c in enumerate(CASES)]
    plain = run_suite(MockDrexClient(RULES), CASES)
    grouped_report = run_suite(MockDrexClient(RULES), grouped)
    for q in plain:
        overall = {k: v for k, v in grouped_report[q].items() if k != "by_group"}
        assert overall == plain[q]  # grouping does not change the overall row
        assert set(grouped_report[q]["by_group"]) == {"a", "b"}
        assert grouped_report[q]["by_group"]["a"]["n"] == 1
    assert "by_group" not in plain["team"]  # no groups -> no key (schema additive)


def test_mock_wrong_when_rules_miss():
    bad_rules = {"team": {"spam": "other"}}  # no keyword matches either ticket
    report = run_suite(MockDrexClient(bad_rules), CASES)
    assert report["team"]["accuracy"] < 1.0  # falls back to uniform -> miss at least once
    # refund has no rules and no criteria -> empty probs: still counted, and the
    # missing expected label costs the full (0-1)^2 brier penalty
    assert report["refund"]["brier"] == pytest.approx(1.0)


def _fake_response(monkeypatch, payload):
    import json as _json
    import urllib.request

    class FakeResp:
        def read(self):
            return _json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=120: FakeResp())


def test_client_parses_real_response_contract(monkeypatch):
    # response shape from drex-decision-models docs/request-format.md
    from drexevals import DecisionRequest, DrexClient

    _fake_response(monkeypatch, {
        "answers": {
            "team": {
                "type": "choice", "choice": "billing", "confidence": 0.9889,
                "probabilities": {"billing": 0.9926, "technical": 0.0024, "other": 0.005},
            },
            "refund": {"type": "noul", "noul": 0.9931},
            "urgency": {
                "type": "score", "score": 1.3362, "legend": ["Routine", "Soon", "Urgent"],
                "probabilities": {"0": 0.2489, "1": 0.166, "2": 0.5851},
            },
        },
        "usage": {"input_tokens": 87, "output_tokens": 166},
    })
    answer = DrexClient(base_url="http://x").decide(DecisionRequest(state={}, questions=[]))
    chosen, probs = answer.per_question["team"]
    assert chosen == "billing"
    assert probs["billing"] == pytest.approx(0.9926)
    chosen, probs = answer.per_question["refund"]
    assert chosen == "noui"
    assert probs == {"noui": pytest.approx(0.9931), "noun": pytest.approx(0.0069)}
    chosen, probs = answer.per_question["urgency"]
    assert chosen == "Urgent"
    assert probs["Soon"] == pytest.approx(0.166)


def test_client_rejects_invalid_probability(monkeypatch):
    from drexevals import DecisionRequest, DrexClient

    _fake_response(monkeypatch, {"answers": {"refund": {"type": "noul", "noul": "NaN"}}})
    with pytest.raises(ValueError, match="refund"):
        DrexClient(base_url="http://x").decide(DecisionRequest(state={}, questions=[]))


def test_gate_decision_rule():
    from drexevals import gate

    assert gate(0.97, tau=0.9) == "act"
    assert gate(0.5, tau=0.9) == "ask"


def test_risk_at():
    from drexevals import risk_at

    pairs = [(0.9, True), (0.8, True), (0.6, False)]
    assert risk_at(pairs, 0.0) == (1 / 3, 1.0)  # act on all: one wrong
    assert risk_at(pairs, 0.7) == (0.0, 2 / 3)  # the wrong one is below tau
    assert risk_at(pairs, 0.95) == (0.0, 0.0)  # nothing acts


def test_calibrate_threshold():
    from drexevals import calibrate_threshold

    pairs = [(0.9, True), (0.8, True), (0.6, False)]
    tau, cov, risk = calibrate_threshold(pairs, max_risk=0.5)
    assert (tau, cov, risk) == (0.6, 1.0, pytest.approx(1 / 3))
    tau, cov, risk = calibrate_threshold(pairs, max_risk=0.2)  # must skip the wrong one
    assert (tau, cov, risk) == (0.8, 2 / 3, 0.0)
    # a wrong answer at max confidence leaves no acting threshold
    pairs = [(0.99, False), (0.9, True)]
    assert calibrate_threshold(pairs, max_risk=0.0) == (1.1, 0.0, 0.0)
