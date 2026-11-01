"""EASY VERSION: Human approval flow. LLM ko approve/execute tools kabhi nahi milte, ye sab insaan karta hai."""
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
from mcp.types import TextContent

from booking_client import authenticated_booking_client

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


# ============================================
# HELPER: tool ke result se dictionary nikalo
# ============================================

def get_result(result) -> dict:
    """MCP tool ka jawab kabhi structured data mein aata hai, kabhi text (JSON) mein.
    Ye function dono surton mein ek saaf dictionary wapas deta hai."""

    if result.is_error:
        raise RuntimeError("MCP tool returned error")

    # Surat 1: structured data mila
    if result.structured_content:
        data = result.structured_content
        # Kabhi asal data "result" ke andar lipta hota hai
        if isinstance(data.get("result"), dict):
            return data["result"]
        return data

    # Surat 2: text mila, usay JSON se dictionary banao
    for item in result.content:
        if isinstance(item, TextContent):
            data = json.loads(item.text)
            if isinstance(data, dict):
                return data

    raise RuntimeError("No structured result")


# ============================================
# MAIN: request -> approve -> execute
# ============================================

async def main():

    # ---------- Step 1: user se details lo ----------
    city = input("City [Dubai]: ").strip() or "Dubai"
    nights = int(input("Nights [5]: ").strip() or "5")

    # ---------- Step 2: TRAVELER request banata hai ----------
    async with authenticated_booking_client("traveler") as traveler:
        request = get_result(await traveler.call_tool(
            "request_hotel_booking",
            {"city": city, "nights": nights, "hotel_class": "4-star"},
        ))

    print("PENDING REQUEST:", request)

    if not request.get("success"):
        return

    request_id = request["request_id"]
    print("Demo action only; NO real booking or payment will occur.")

    # ---------- Step 3: INSAAN faisla karta hai ----------
    # Note: ye sirf demo hai. Asal app mein approver alag login wala banda hota hai.
    answer = input("Are you the authorized approver? Type APPROVE to authorize: ").strip()
    approved = (answer == "APPROVE")

    # ---------- Step 4: ADMIN approve/reject karta hai ----------
    async with authenticated_booking_client("admin") as admin:
        decision = get_result(await admin.call_tool(
            "approve_booking",
            {"request_id": request_id, "approved": approved},
        ))
        print("DECISION:", decision)

        if decision.get("status") != "approved":
            return

        # ---------- Step 5: dobara pakki tasdeeq, phir EXECUTE ----------
        confirm = input("Type EXECUTE for the one-time DEMO booking: ").strip()

        if confirm != "EXECUTE":
            print("Not executed.")
            return

        outcome = get_result(await admin.call_tool(
            "execute_approved_booking",
            {"request_id": request_id},
        ))
        print("BOOKING RESULT:", outcome)


if __name__ == "__main__":
    asyncio.run(main())