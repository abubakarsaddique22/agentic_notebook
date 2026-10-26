"""
F.5 Async: kai requests ek saath + Semaphore se limit
=====================================================
    python -m part_f_httpx_client.f5_async_concurrency

Note: .py file mein async code asyncio.run(main()) se chalta hai.
Theory: part_f_httpx_client/NOTES.md (F.5)
"""
import asyncio
import time

import httpx

from common import BASE, check_server


async def sequential():
    """Ek ke baad ek: har await pichli request khatam hone ka intezar karta hai."""
    async with httpx.AsyncClient(base_url=BASE) as ac:
        return [(await ac.get("/slow", params={"seconds": 0.5})).json() for _ in range(5)]


async def concurrent():
    """Ek saath: saari requests bhej do, phir sab ka intezar."""
    async with httpx.AsyncClient(base_url=BASE) as ac:
        tasks = [ac.get("/slow", params={"seconds": 0.5}) for _ in range(5)]
        return [r.json() for r in await asyncio.gather(*tasks)]


async def limited(n_requests: int = 8, max_parallel: int = 3):
    """Ek waqt mein sirf max_parallel requests (rate limit se bachne ke liye)."""
    sem = asyncio.Semaphore(max_parallel)
    async with httpx.AsyncClient(base_url=BASE) as ac:
        async def one(i):
            async with sem:                      # sirf 3 ek waqt mein andar
                await ac.get("/slow", params={"seconds": 0.3})
                return i
        return await asyncio.gather(*(one(i) for i in range(n_requests)))


async def main():
    t = time.perf_counter(); await sequential()
    print(f"5 requests ek ke baad ek : {time.perf_counter() - t:.2f}s")
    t = time.perf_counter(); await concurrent()
    print(f"5 requests ek saath      : {time.perf_counter() - t:.2f}s")
    t = time.perf_counter(); await limited()
    print(f"8 requests, max 3 parallel: {time.perf_counter() - t:.2f}s  (~ 3 batches x 0.3s)")


if __name__ == "__main__":
    check_server()
    asyncio.run(main())
