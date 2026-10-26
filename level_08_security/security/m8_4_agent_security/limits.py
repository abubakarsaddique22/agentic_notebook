"""Runtime limits: stop runaway agents (step, time, cost).

An agent stuck in a tool loop burns money and can be an attack (S8). We cap:
  - steps   : LangGraph recursion_limit
  - time    : a wall-clock deadline checked around invoke
  - cost    : a rough token budget tracked per run

These are blunt but essential. Real systems also add per-tool rate limits.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

MAX_STEPS = 8            # recursion_limit passed to the agent
WALL_CLOCK_SECONDS = 60  # hard deadline for a single user turn


class LimitExceeded(Exception):
    pass


@dataclass
class RunBudget:
    max_steps: int = MAX_STEPS
    deadline_s: float = WALL_CLOCK_SECONDS
    _start: float = 0.0

    def start(self) -> "RunBudget":
        self._start = time.monotonic()
        return self

    def check_time(self) -> None:
        if self._start and (time.monotonic() - self._start) > self.deadline_s:
            raise LimitExceeded(f"Turn exceeded {self.deadline_s}s deadline.")

    @property
    def config(self) -> dict:
        """Pass to agent.invoke(..., config=budget.config) to cap steps."""
        return {"recursion_limit": self.max_steps}
