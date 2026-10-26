"""The combined guardrail layer: deterministic rails + Llama Guard moderation.

Order (cheapest first, so we rarely pay for the model call):
  INPUT :  rails.check_input  ->  Llama Guard moderate_input
  OUTPUT:  rails.check_output ->  Llama Guard moderate_output

This is what the secure agent (M8.9) wires around every turn.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# rails: deterministic (pattern-based) checks. Muft aur foran, bina model ke.
from m8_3_guardrails import rails
# moderate_input / moderate_output: gpt-oss model se message ko safe/unsafe
#   classify karte hain (layer 2, jab pattern check pass ho jaye).
from m8_3_guardrails.moderation import moderate_input, moderate_output

BLOCK_MESSAGE = (
    "Sorry, I can't help with that. If you have a genuine order or support "
    "question I'm happy to help, or I can connect you to a human agent."
)


@dataclass
class GateResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


def guard_input(message: str, use_model: bool = True) -> GateResult:
    d = rails.check_input(message)
    if d.blocked:
        return GateResult(False, d.reasons)
    if use_model:
        m = moderate_input(message)
        if m.flagged:
            return GateResult(False, [f"moderation-input:{c}" for c in m.categories] or ["moderation-input"])
    return GateResult(True, [])


def guard_output(message: str, use_model: bool = True) -> GateResult:
    d = rails.check_output(message)
    if d.blocked:
        return GateResult(False, d.reasons)
    if use_model:
        m = moderate_output(message)
        if m.flagged:
            return GateResult(False, [f"moderation-output:{c}" for c in m.categories] or ["moderation-output"])
    return GateResult(True, [])
