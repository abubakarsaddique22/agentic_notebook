"""Practice bot package.

__init__.py tab chalti hai jab koi `import bot` kare. Yahan:
1. Python ko pata chalta hai ye folder package hai
2. Shortcut imports: `from bot import Conversation` (bajaye `from bot.models import Conversation`)
3. Package level cheezein jaise __version__

`from .config` mein '.' ka matlab: "isi package ke andar se" (relative import).
"""
from .config import BotConfig
from .models import Conversation, Message

__version__ = "0.1.0"
__all__ = ["BotConfig", "Conversation", "Message"]
