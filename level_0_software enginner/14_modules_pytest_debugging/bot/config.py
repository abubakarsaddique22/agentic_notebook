"""Bot ki saari settings ek jagah (frozen dataclass + validation + JSON save/load)."""
import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, kw_only=True)
class BotConfig:
    bot_name: str = "SupportBot"
    model: str = "gpt-4o-mini"
    temperature: float = 0.5
    max_history: int = 10
    system_prompt: str = "Tum ek watch store ke helpful support agent ho."

    def __post_init__(self):
        if not 0 <= self.temperature <= 2:
            raise ValueError("temperature 0 aur 2 ke beech honi chahiye")
        if self.max_history < 1:
            raise ValueError("max_history kam az kam 1 ho")

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "BotConfig":
        return cls(**json.loads(Path(path).read_text(encoding="utf-8")))
