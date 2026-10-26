"""pytest setup: .env load karo aur parent folder (support_app.py) ko import path mein daalo."""
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve()
load_dotenv(HERE.parents[2] / ".env")
sys.path.insert(0, str(HERE.parents[1]))
