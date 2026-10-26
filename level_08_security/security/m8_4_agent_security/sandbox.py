"""Sandbox model-generated code (roadmap M8.4).

Never run code the model wrote on your own machine or with your own privileges.
Run it inside a locked-down container: no network, read-only filesystem, memory
and CPU caps, a timeout, and a non-root user.

This module builds the `docker run` command. Executing it needs Docker Desktop
(free for personal use on Windows). We don't auto-run anything; per your setup,
you run the printed command yourself.
"""
from __future__ import annotations

import shlex

# Hardened flags, each one closes a specific escape/abuse route.
HARDENING = [
    "--network", "none",          # no exfiltration / no callbacks
    "--read-only",                # filesystem is read-only
    "--tmpfs", "/tmp:size=16m",   # only a tiny scratch space
    "--memory", "256m",           # memory cap
    "--cpus", "0.5",              # CPU cap
    "--pids-limit", "64",         # no fork bombs
    "--user", "65534:65534",      # run as 'nobody', never root
    "--cap-drop", "ALL",          # drop all Linux capabilities
    "--security-opt", "no-new-privileges",
]


def build_docker_command(code: str, image: str = "python:3.12-slim", timeout_s: int = 10) -> str:
    """Return a one-line `docker run` command that executes `code` safely.

    The code is passed via stdin to avoid quoting problems.
    """
    inner = f"timeout {timeout_s} python -"
    flags = " ".join(HARDENING)
    # `-i` so the container reads code from stdin; we pipe it in from PowerShell.
    return f"echo {shlex.quote(code)} | docker run --rm -i {flags} {image} {inner}"


if __name__ == "__main__":
    demo = "print(sum(range(10)))"
    print("Run this in PowerShell (needs Docker Desktop):\n")
    print(build_docker_command(demo))
