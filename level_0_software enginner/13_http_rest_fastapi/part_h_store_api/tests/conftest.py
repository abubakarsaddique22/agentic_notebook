import pytest
from fastapi.testclient import TestClient

from app.deps import get_llm
from app.main import app


class InstantLLM:
    """Asli FakeLLM (0.5s) ki jagah: foran jawab, aur yaad rakhta hai kya poocha gaya."""

    def __init__(self):
        self.calls: list[str] = []

    async def complete(self, message, history):
        self.calls.append(message)
        return "fake jawab"

    async def stream(self, message):
        for t in ["fake", "stream"]:
            yield t


@pytest.fixture
def fake_llm():
    return InstantLLM()


@pytest.fixture
def client(fake_llm):
    app.dependency_overrides[get_llm] = lambda: fake_llm
    with TestClient(app) as c:            # `with` se lifespan bhi chalta hai
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth():
    return {"X-API-Key": "test-key-1"}
