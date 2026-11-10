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
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read())

        out = Answer()
        for name, result in payload.get("answers", {}).items():
            options: dict[str, float] = {
                o["label"]: float(o["probability"])
                for o in result.get("options", [])
            }
            for label, p in options.items():
                if not (math.isfinite(p) and 0.0 <= p <= 1.0):
                    raise ValueError(
                        f"question {name!r}: option {label!r} has invalid probability {p!r}"
                    )
            argmax = max(options, key=options.get) if options else ""
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
