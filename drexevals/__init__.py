"""drexevals: evaluation bridge for Drex decision models (arXiv:2611.07854).

Drex answers named typed questions (choice / yes-no / score) about a state and
returns a calibrated probability for every option. This repo wires that API
into runnable decision suites (triage, gates, classification) and scores
accuracy plus calibration, offline-first.

The models themselves are open: https://github.com/nace-ai/drex-decision-models
(hosted API at https://drex.nace.ai/docs, or serve.py locally — a 9B distill
runs on Apple silicon, the 35B MoE needs ~24GB RAM or the Q4 GGUF).
"""

from .client import DrexClient, MockDrexClient
from .types import DecisionRequest, Question, Answer
from .runner import run_suite

__version__ = "0.1.0"
__all__ = [
    "DrexClient",
    "MockDrexClient",
    "DecisionRequest",
    "Question",
    "Answer",
    "run_suite",
]
