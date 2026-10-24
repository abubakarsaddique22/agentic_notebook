"""
F.2 Timeouts: hamesha lagayein
==============================
    python -m part_f_httpx_client.f2_timeouts

Theory: part_f_httpx_client/NOTES.md (F.2)
"""
import httpx

from common import get_client

client = get_client()

# /slow 3 second leta hai, hum sirf 1 second intezar karein ge
try:
    client.get("/slow", params={"seconds": 3}, timeout=1)
except httpx.TimeoutException as e:
    print("Timeout hua:", type(e).__name__)

# Detail mein: connect ka alag, read ka alag
llm_timeout = httpx.Timeout(connect=5, read=60, write=10, pool=5)   # LLM ka jawab lamba ho sakta hai
print(llm_timeout)

client.close()
