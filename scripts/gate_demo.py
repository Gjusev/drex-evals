#!/usr/bin/env python3
"""Live act/ask gate demo: Drex scores, the gate decides.

Wires the two halves of this repo together:
- Drex (hosted or local) scores a decision as p(phish) — the System 1 read
- drexevals.gate applies the threshold tau* calibrated ON MEASURED DATA by
  scripts/escalation_analysis.py (results/escalation_policies.json,
  phishield suite, risk budget 5%: tau ~0.97 hosted)

This is a demonstration of the integration, not a benchmark: the scenarios
are illustrative and the thresholds are bin-granular (see results/README.md).

Usage: python3 scripts/gate_demo.py            # env: DREX_BASE_URL, DREX_API_KEY
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drexevals import DrexClient, Question, gate  # noqa: E402

PHISH_Q = Question(
    name="phish", type="noul",
    instructions="Is this email a phishing attempt targeting the recipient?",
)

SCENARIOS = [
    ("obvious phish", {
        "subject": "URGENT: account suspended in 24h",
        "from": '"PayPal Support" <no-reply@paypal-verify-alert.example>',
        "reply_to": "",
        "first_url_host": "paypal-verify-alert.example",
        "body": "Dear customer, we detected unusual activity. Confirm your password within 24 hours "
                "or your account will be permanently closed.",
    }),
    ("clearly legit", {
        "subject": "Your order #W6619 has shipped",
        "from": "notifications@shop.example",
        "reply_to": "",
        "first_url_host": "shop.example",
        "body": "Hi, your order #W6619 shipped today and arrives Thursday. Track it any time from your account.",
    }),
    ("gray zone", {
        "subject": "Invoice overdue - immediate payment required",
        "from": '"Accounts Receivable" <billing@vendor-co.example>',
        "reply_to": "billing@vendor-co.example",
        "first_url_host": "vendor-co.example",
        "body": "Your invoice INV-2291 is 14 days overdue. Pay today to avoid a late fee: "
                "https://vendor-co.example/pay/INV-2291",
    }),
]


def main():
    policies = json.loads(Path("results/escalation_policies.json").read_text(encoding="utf-8"))
    tau = policies["suites/phishield_test_183.json:phish"]["drex hosted API (drex.nace.ai)"]["calibrated"]["5%"]["tau"]

    client = DrexClient()
    print(f"threshold tau={tau:.2f} (phishield suite, hosted, risk<=5%, bin granularity)\n")
    for name, state in SCENARIOS:
        answer = client.decide(__import__("drexevals.types", fromlist=["DecisionRequest"]).DecisionRequest(
            state=state, questions=[PHISH_Q]))
        chosen, probs = answer.per_question["phish"]
        p_phish = probs.get("noui", 0.0)
        # gate on confidence in the argmax class, mirroring the runner's conf:
        # auto-act on "block" AND on "file as safe" — only the unsure middle escalates
        verdict = "block" if p_phish >= 0.5 else "allow"
        conf = max(p_phish, 1.0 - p_phish)
        decision = gate(conf, tau)
        print(f"{name:14} p(phish)={p_phish:.3f} verdict={verdict:5} conf={conf:.3f} -> {decision.upper()}"
              + ("  (escalate to a human)" if decision == "ask" else f"  ({verdict})"))


if __name__ == "__main__":
    main()
