"""
1) Sampling: high traffic par sirf kuch % traces bhejo (cost + storage bachao).
     Langfuse(sample_rate=0.3)   ya   env var LANGFUSE_SAMPLE_RATE=0.3
   Sampling poore TRACE par hoti hai — trace kabhi aadha nahi kat'ta.
   NOTE: Experiments (folder 06) chalate waqt sample_rate=1.0 rakho, warna results adhoore.

2) Flush: SDK observations background thread se batch mein bhejta hai.
   Server (FastAPI) mein masla nahi. Short scripts, cron jobs, serverless mein process jaldi
   khatam ho to data gum ho sakta hai -> langfuse.flush() (ya shutdown()) zaroor.
"""
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from langfuse import Langfuse, observe  # noqa: E402

langfuse = Langfuse(sample_rate=0.3)  # sabse pehle (singleton)


@observe(name="sampled-request")
def handle(i: int) -> int:
    return i * 2


if __name__ == "__main__":
    for i in range(20):
        handle(i)

    langfuse.flush()  # sab pending data abhi bhej do (blocking)
    print("20 calls kiye. UI mein ~6 traces (30%) dikhne chahiye.")
    # Worker/daemon band karte waqt: langfuse.shutdown()  -> flush + background threads band
