"""Shared fixtures. pytest is file ko khud dhoond leta hai, import nahi karna parta.
Har test ko NAYA fixture milta hai, is liye ek test doosre ko kharab nahi karta."""
import pytest

from bot.config import BotConfig
from bot.models import Conversation


@pytest.fixture
def config():
    return BotConfig(max_history=4)


@pytest.fixture
def convo(config):          # fixture doosre fixture ko use kar sakta hai
    return Conversation("923001234567", config.system_prompt, max_history=config.max_history)
