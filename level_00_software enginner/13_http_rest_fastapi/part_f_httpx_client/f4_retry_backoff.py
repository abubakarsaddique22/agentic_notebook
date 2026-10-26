"""
F.4 Retry + Exponential Backoff + Jitter + Retry-After
======================================================
Interview mein aksar ye function khud likhwate hain.
    python -m part_f_httpx_client.f4_retry_backoff

Theory: part_f_httpx_client/NOTES.md (F.4)
"""
import random
import time

import httpx

from common import get_client

client = get_client()

RETRYABLE = {429, 500, 502, 503, 504}


def request_with_retry(method: str, url: str, max_retries: int = 4,
                       base_delay: float = 0.5, **kwargs) -> httpx.Response:
    for attempt in range(max_retries + 1):
        try:
            r = client.request(method, url, **kwargs)
            if r.status_code not in RETRYABLE:
                return r                                   # kamyaab, ya aisi ghalti jis par retry bekaar
            reason = f"HTTP {r.status_code}"
            retry_after = r.headers.get("Retry-After")
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            reason, retry_after = type(e).__name__, None

        if attempt == max_retries:
            raise RuntimeError(f"{max_retries} retries ke baad bhi fail: {reason}")

        # Server ne bataya kitna ruko? Wahi maano. Warna 0.5, 1, 2, 4... + thora random
        delay = float(retry_after) if retry_after else base_delay * 2 ** attempt + random.uniform(0, 0.1)
        print(f"   attempt {attempt + 1}: {reason} -> {delay:.2f}s intezar")
        time.sleep(delay)


client.post("/reset-counters")      # demo ko saaf shuru karne ke liye

print("/flaky (pehli 2 calls 503):")
print("  ", request_with_retry("GET", "/flaky").json())
print("/rate-limited (429 + Retry-After):")
print("  ", request_with_retry("GET", "/rate-limited").json())

client.close()
