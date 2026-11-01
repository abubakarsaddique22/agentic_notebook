"""EASY VERSION: Demo hotel booking MCP server (port 8004). Koi real booking nahi hoti."""
import os
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pydantic import AnyHttpUrl
from mcp.server import MCPServer
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.auth.middleware.auth_context import get_access_token


# ============================================
# 1. SETTINGS
# ============================================

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SERVER_URL = "http://127.0.0.1:8004/mcp"

USER_TOKEN = os.getenv("BOOKING_USER_TOKEN", "")
ADMIN_TOKEN = os.getenv("BOOKING_ADMIN_TOKEN", "")

if not USER_TOKEN or not ADMIN_TOKEN or USER_TOKEN == ADMIN_TOKEN:
    raise RuntimeError(".env mein do alag tokens rakhein: BOOKING_USER_TOKEN aur BOOKING_ADMIN_TOKEN")

# Token -> (kaun hai, kya kya kar sakta hai)
USERS = {
    USER_TOKEN: ("traveler", ["booking:read"]),
    ADMIN_TOKEN: ("admin", ["booking:read", "booking:approve", "booking:execute"]),
}


# ============================================
# 2. TOKEN CHECK (har request par chalta hai)
# ============================================

class SimpleVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        user = USERS.get(token)
        if user is None:
            return None  # ghalat token = andar aana mana

        name, scopes = user
        return AccessToken(token=token, client_id=name, scopes=scopes, resource=SERVER_URL)


server = MCPServer(
    "Easy Demo Booking MCP",
    token_verifier=SimpleVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com"),  # sirf placeholder, real login server nahi
        resource_server_url=AnyHttpUrl(SERVER_URL),
        required_scopes=["booking:read"],
        validate_token_resource=True,
    ),
)


# ============================================
# 3. DATA (memory mein, server band = data khatam)
# ============================================

bookings = {}  # request_id -> booking ki details


def check_permission(scope: str) -> AccessToken:
    """Dekhta hai ke caller ke paas ye permission (scope) hai ya nahi."""
    token = get_access_token()
    if token is None or scope not in token.scopes:
        raise PermissionError(f"Permission nahi hai: '{scope}' chahiye")
    return token


def is_expired(booking: dict) -> bool:
    return datetime.now(timezone.utc) > datetime.fromisoformat(booking["expires_at"])


# ============================================
# 4. TOOLS
# Flow: request (user) -> approve (admin) -> execute (admin)
# ============================================

@server.tool()
def request_hotel_booking(city: str, nights: int, hotel_class: str = "4-star") -> dict:
    """Pending DEMO booking request banata hai. Asal hotel book nahi hota."""
    token = check_permission("booking:read")

    if nights < 1 or nights > 30 or hotel_class not in ["3-star", "4-star", "5-star"]:
        return {"success": False, "error": "Ghalat nights ya hotel_class"}

    request_id = secrets.token_urlsafe(16)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    bookings[request_id] = {
        "request_id": request_id,
        "city": city.strip(),
        "nights": nights,
        "hotel_class": hotel_class,
        "status": "pending",
        "expires_at": expires_at.isoformat(),
        "booking_id": None,
        "requested_by": token.client_id,
    }

    return {"success": True, **bookings[request_id], "demo": True}


@server.tool()
def get_booking_request(request_id: str) -> dict:
    """Booking request dikhata hai. Traveler sirf apni request dekh sakta hai."""
    token = check_permission("booking:read")
    booking = bookings.get(request_id)

    is_owner = booking is not None and booking["requested_by"] == token.client_id
    is_admin = "booking:approve" in token.scopes

    if booking is None or not (is_owner or is_admin):
        return {"success": False, "error": "Request nahi mili ya permission nahi"}

    return {"success": True, **booking, "demo": True}


@server.tool()
def approve_booking(request_id: str, approved: bool) -> dict:
    """SIRF ADMIN. Pending request ko approve ya reject karta hai."""
    check_permission("booking:approve")
    booking = bookings.get(request_id)

    if booking is None or booking["status"] != "pending":
        return {"success": False, "error": "Koi pending request nahi"}

    if is_expired(booking):
        booking["status"] = "expired"
        return {"success": False, "error": "Request expire ho gayi"}

    booking["status"] = "approved" if approved else "rejected"
    return {"success": True, "request_id": request_id, "status": booking["status"], "demo": True}


@server.tool()
def execute_approved_booking(request_id: str) -> dict:
    """SIRF ADMIN. Approved request ko sirf EK dafa execute karta hai (DEMO)."""
    check_permission("booking:execute")
    booking = bookings.get(request_id)

    if booking is None or booking["status"] != "approved":
        return {"success": False, "error": "Approval nahi hai ya pehle hi execute ho chuki"}

    if is_expired(booking):
        booking["status"] = "expired"
        return {"success": False, "error": "Approval expire ho gayi"}

    booking["status"] = "executed"
    booking["booking_id"] = "DEMO-" + secrets.token_hex(6).upper()

    return {"success": True, **booking, "demo": True, "real_booking": False}


# ============================================
# 5. RUN SERVER
# ============================================

if __name__ == "__main__":
    server.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8004,
        stateless_http=True,
        json_response=True,
    )