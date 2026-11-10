#!/usr/bin/env python3
"""Build suites/phishield_test_183.json from laya-phishield's prepared test split.

Source: ../laya-phishield/data/prepared/test.jsonl (183 emails: 78 phishing
from the Nazario corpus, 105 legitimate from Enron). Labels are
corpus-membership labels, not per-message human annotation — anything from
Nazario is label 1, anything from Enron label 0 (their evals/prepare_data.py).
The split is per-class temporal (newest 30% test). English, 1998-2002 Enron
vs 2000s Nazario — style alone is highly separable, so read accuracy as an
upper bound; the interesting number is calibration.

If test.jsonl is missing (it is gitignored there), regenerate it in
laya-phishield first: python evals/prepare_data.py  (downloads ~473 MB).

Usage: python3 scripts/import_laya_phishield.py
"""
import email
import email.policy
import json
import re
import subprocess
from pathlib import Path

EVALS = Path(__file__).resolve().parent.parent
PHISHIELD = EVALS.parent / "laya-phishield"

PHISH_Q = {
    "name": "phish",
    "type": "noul",
    "instructions": "Is this email a phishing attempt targeting the recipient?",
}

TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://([^/\s\"'>]+)")


def body_text(msg: email.message.Message, cap: int = 1200) -> str:
    plain, html = "", ""
    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        raw = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        try:
            text = raw.decode(charset, errors="replace")
        except LookupError:  # corpus has invented charsets (iso-18899997-1)
            text = raw.decode("latin-1", errors="replace")
        if ctype == "text/plain" and not plain:
            plain = text
        if ctype == "text/html" and not html:
            html = text
    text = plain or TAG_RE.sub(" ", html)
    return " ".join(text.split())[:cap]


def build_state(raw: str) -> dict:
    msg = email.message_from_string(raw)
    body = body_text(msg)
    url_host = URL_RE.search(body)
    return {
        "subject": str(msg.get("Subject", "")).strip(),
        "from": str(msg.get("From", "")).strip(),
        "reply_to": str(msg.get("Reply-To", "")).strip(),
        "first_url_host": url_host.group(1).lower() if url_host else "",
        "body": body,
    }


def main():
    src = PHISHIELD / "data" / "prepared" / "test.jsonl"
    if not src.exists():
        raise SystemExit(f"{src} missing — run `python evals/prepare_data.py` in laya-phishield first (see module docstring)")
    sha = subprocess.run(
        ["git", "-C", str(PHISHIELD), "log", "-1", "--format=%h", "--", "data/prepared"],
        capture_output=True, text=True,
    ).stdout.strip() or "uncommitted"

    rows = [json.loads(line) for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
    cases = [{
        "state": build_state(r["raw"]),
        "questions": [PHISH_Q],
        "expected": {"phish": "noui" if r["label"] == 1 else "noun"},
    } for r in rows]

    suite = {
        "name": "phishield_test_183",
        "description": (
            f"Phishing detection on laya-phishield's canonical temporal test split "
            f"(183 emails: 78 Nazario phish, 105 Enron legit), imported from "
            f"data/prepared/test.jsonl @ {sha}. Labels are corpus-membership labels "
            "(Nazario=phish, Enron=legit), not per-message human annotation. "
            "Enron-vs-Nazario style is highly separable — read accuracy as an "
            "upper bound; calibration is the interesting number."
        ),
        "questions_schema": [PHISH_Q],
        "cases": cases,
    }
    out = EVALS / "suites" / "phishield_test_183.json"
    out.write_text(json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")
    phish = sum(1 for c in cases if c["expected"]["phish"] == "noui")
    print(f"{len(cases)} cases ({phish} phish / {len(cases) - phish} legit) -> {out}")


if __name__ == "__main__":
    main()
