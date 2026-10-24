"""
Shared helpers jo Parts A-F ki saari lesson files use karti hain.

Import aise hota hai:   from common import BASE, USER, ADMIN, get_client, show
Ye tab hi chalta hai jab aap file ko FOLDER KI ROOT se `python -m ...` se chalayein:

    python -m part_a_http_basics.a2_request_response
"""
import os
import sys

import httpx

# Windows cmd mein Urdu/special characters print karte waqt crash na ho
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# Localhost wali requests kabhi proxy se na guzrein (office/VPN wale networks ke liye)
os.environ["NO_PROXY"] = os.environ["no_proxy"] = ",".join(
    filter(None, [os.environ.get("NO_PROXY", ""), "127.0.0.1", "localhost"]))

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"

USER = {"Authorization": "Bearer practice-key-123"}
ADMIN = {"Authorization": "Bearer admin-key-999"}


def check_server() -> None:
    """Practice server chal raha hai? Nahi to saaf message de kar ruk jao."""
    try:
        httpx.get(f"{BASE}/docs", timeout=2)
    except httpx.TransportError:
        print("[X] Practice server nahi chal raha!")
        print("    Doosri cmd window kholein, isi folder mein jayein aur chalayein:")
        print("    uvicorn practice_server:app --port 8765 --reload")
        sys.exit(1)


def get_client() -> httpx.Client:
    """Server check kar ke ek reusable client do (poore lesson mein yahi use karein)."""
    check_server()
    return httpx.Client(base_url=BASE, timeout=10)


def show(r: httpx.Response, max_body: int = 500) -> None:
    """Request aur response ko 'raw HTTP' ki shakal mein dikhao."""
    req = r.request
    print(">>> REQUEST")
    print(f"{req.method} {req.url}")
    for k, v in req.headers.items():
        print(f"{k}: {v}")
    if req.content:
        print("\n" + req.content.decode(errors="replace")[:max_body])
    print("\n<<< RESPONSE")
    print(f"HTTP {r.status_code} {r.reason_phrase}")
    for k, v in r.headers.items():
        print(f"{k}: {v}")
    if r.content:
        print("\n" + r.text[:max_body])


def title(text: str) -> None:
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)
