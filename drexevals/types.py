"""Types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Question:
    """Named typed question in Drex's /v1/systemone request format."""

    name: str
    type: str  # "choice" | "noul" (yes/no) | "score"
    instructions: str
    criteria: Any = None  # dict for choice, list for score, None for noul

    def to_api(self) -> dict:
        q = {"type": self.type, "instructions": self.instructions}
        if self.criteria is not None:
            q["criteria"] = self.criteria
        return q


@dataclass
class DecisionRequest:
    state: dict
    questions: list[Question]

    def to_api(self) -> dict:
        return {
            "state": self.state,
            "questions": {q.name: q.to_api() for q in self.questions},
        }


@dataclass
class Answer:
    """Parsed response: question name -> (argmax option, {option: probability})."""

    per_question: dict[str, tuple[str, dict[str, float]]] = field(default_factory=dict)
