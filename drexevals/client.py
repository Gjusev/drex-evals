"""Drex /v1/systemone client (hosted or serve.py local) + offline mock."""

from __future__ import annotations

import math
import os
from abc import ABC, abstractmethod

from .types import Answer, DecisionRequest


class BaseClient(ABC):
    @abstractmethod
    def decide(self, request: DecisionRequest) -> Answer: ...


class DrexClient(BaseClient):
    """POSTs to {base_url}/v1/systemone.

    base_url: https://drex.nace.ai (hosted, needs DREX_API_KEY) or a local
    serve.py instance (http://localhost:8000, no key).
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("DREX_BASE_URL", "https://drex.nace.ai")).rstrip("/")
        self.api_key = api_key or os.environ.get("DREX_API_KEY", "")

    def decide(self, request: DecisionRequest) -> Answer:
        import json
        import time
        import urllib.error
        import urllib.request

        req = urllib.request.Request(
            f"{self.base_url}/v1/systemone",
            data=json.dumps(request.to_api()).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        payload = None
        for attempt, backoff in enumerate((0, 2, 8), start=1):
            if backoff:
                time.sleep(backoff)
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    payload = json.loads(resp.read())
                break
            except urllib.error.HTTPError as exc:
                # transient on the hosted API under sequential load: retry,
                # otherwise surface the status
                if exc.code in (408, 425, 429) or 500 <= exc.code < 600:
                    if attempt == 3:
                        raise
                    continue
                raise
        if payload is None:  # pragma: no cover - defensive
            raise RuntimeError(f"{self.base_url}/v1/systemone: no response after retries")

        out = Answer()
        for name, result in payload.get("answers", {}).items():
            qtype = result.get("type")
            if qtype == "noul":
                # server sends only the probability of "yes"; this repo labels
                # the noul outcomes "noui" / "noun" (suite + mock convention)
                p_yes = float(result["noul"])
                options: dict[str, float] = {"noui": p_yes, "noun": 1.0 - p_yes}
            elif qtype == "score":
                # probabilities are keyed by level index, legend maps to labels
                legend = result.get("legend") or []
                options = {
                    (legend[int(k)] if int(k) < len(legend) else k): float(v)
                    for k, v in result.get("probabilities", {}).items()
                }
            else:  # choice: probabilities keyed by option label
                options = {
                    label: float(p)
                    for label, p in result.get("probabilities", {}).items()
                }
            for label, p in options.items():
                if not (math.isfinite(p) and 0.0 <= p <= 1.0):
                    raise ValueError(
                        f"question {name!r}: option {label!r} has invalid probability {p!r}"
                    )
            argmax = result.get("choice") or (max(options, key=options.get) if options else "")
            out.per_question[name] = (argmax, options)
        return out


class MockDrexClient(BaseClient):
    """Deterministic offline stand-in: keyword rules per question name.

    Exists so the eval plumbing is testable without tokens or weights —
    the same role --dry-run plays in agent harnesses.
    """

    def __init__(self, rules: dict[str, dict[str, str]] | None = None) -> None:
        # rules: question name -> {state_keyword: option}
        self.rules = rules or {}

    def decide(self, request: DecisionRequest) -> Answer:
        out = Answer()
        text = " ".join(str(v) for v in request.state.values()).lower()
        for q in request.questions:
            rule = self.rules.get(q.name, {})
            chosen, probs = "", {}
            for keyword, option in rule.items():
                probs[option] = 0.9 if keyword.lower() in text else 0.05
            if not probs:
                options = list(q.criteria) if isinstance(q.criteria, list) else list(q.criteria or {})
                probs = {o: 1 / len(options) for o in options} if options else {}
            if probs:
                chosen = max(probs, key=probs.get)
            out.per_question[q.name] = (chosen, probs)
        return out
