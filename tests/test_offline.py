"""Offline test of the whole eval plumbing (MockDrexClient, zero network)."""

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
        "expected": {"team": "technical", "refund": "noui"},
    },
]

RULES = {
    "team": {"charged": "billing", "refund": "billing", "crashes": "technical", "startup": "technical"},
    "refund": {"refund": "noui"},
}


def test_suite_reports_accuracy_and_calibration():
    report = run_suite(MockDrexClient(RULES), CASES)
    assert report["team"]["accuracy"] == 1.0
    assert report["team"]["n"] == 2
    assert report["refund"]["accuracy"] == 1.0
    # calibration bins must exist and be populated
    assert any(b["n"] > 0 for b in report["team"]["calibration_bins"])
    # confident mock: confidence on correct >= confidence on wrong
    assert report["team"]["confidence_on_correct"] >= report["team"]["confidence_on_wrong"]


def test_mock_wrong_when_rules_miss():
    bad_rules = {"team": {"spam": "other"}}  # no keyword matches either ticket
    report = run_suite(MockDrexClient(bad_rules), CASES)
    assert report["team"]["accuracy"] < 1.0  # falls back to uniform -> miss at least once
