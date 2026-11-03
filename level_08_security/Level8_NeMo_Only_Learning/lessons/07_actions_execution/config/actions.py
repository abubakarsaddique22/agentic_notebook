"""NeMo native action registration. Python stdlib only; no alternate agent stack."""
from nemoguardrails.actions import action

@action()
async def get_support_hours():
    """Read local helpdesk hours. No remote network call or write side effects."""
    return "Monday-Friday, 09:00-18:00 Pakistan time"
