"""Dependencies: auth aur LLM. Tests mein dependency_overrides se badli jaati hain."""
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings
from app.services.llm import FakeLLM

_llm = FakeLLM()


def verify_api_key(settings: Annotated[Settings, Depends(get_settings)],
                   x_api_key: Annotated[str | None, Header()] = None) -> str:
    if not x_api_key or x_api_key not in settings.api_keys:
        raise HTTPException(401, "API key missing ya ghalat", headers={"WWW-Authenticate": "ApiKey"})
    return x_api_key


def get_llm() -> FakeLLM:
    return _llm
