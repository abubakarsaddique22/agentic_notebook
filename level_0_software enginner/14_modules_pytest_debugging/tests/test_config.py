"""B.6 Errors test karna (pytest.raises) + files (tmp_path)."""
from dataclasses import FrozenInstanceError

import pytest

from bot.config import BotConfig


@pytest.mark.parametrize("temp", [-0.1, 2.5, 10])
def test_bad_temperature_raises(temp):
    with pytest.raises(ValueError, match="temperature"):
        BotConfig(temperature=temp)


def test_config_is_frozen(config):
    with pytest.raises(FrozenInstanceError):
        config.temperature = 1.0


def test_save_and_load(tmp_path):
    cfg = BotConfig(model="claude-haiku", temperature=0.2)
    file = tmp_path / "config.json"
    cfg.save(file)
    assert file.exists()
    assert BotConfig.load(file) == cfg
