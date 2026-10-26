"""
Module 5 · Caching Lab
======================

Ek layered cache banata hai aur NAAPTA hai ke asal mein kitna faida hua:

  Layer 0  Policy gate     : kya ye request cache ho bhi sakti hai? (personal data / order no. = NAHI)
  Layer 1  Exact cache     : normalized query + model + prompt_version + kb_version -> answer  (diskcache, TTL)
  Layer 2  Semantic cache  : embedding similarity >= threshold  +  ENTITY GUARD (TW-2041 != TW-2047)
  Layer 3  LLM call        : miss -> generate -> dono caches mein store

Experiments:
  1. Traffic simulation   : 60 requests -> hit rate, $ saved, latency saved
  2. WRONG hits           : semantic cache ne galat jawab kitni dafa diya? (labels se check)
  3. Threshold sweep      : 0.70 ... 0.95 -> hit rate vs wrong-hit rate (trade-off)
  4. Invalidation         : policy update -> kb_version bump -> purane entries miss
  5. Prompt caching math  : static prefix pehle rakho -> provider-side discount

LLM jawab SIMULATED hain (har intent ka fixed jawab, cost/latency M9.1 ke numbers se), kyunke
is lab ka focus caching ke FAISLE hain, generation nahi. Embeddings real (Ollama) ya offline.

Chalane ka tareeqa (PowerShell, root folder, venv active):
    python 05_caching\\caching_lab.py             # Ollama embeddings (behtar)
    python 05_caching\\caching_lab.py --offline   # bina Ollama
"""

from __future__ import annotations

import argparse
import hashlib
import random
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

import diskcache
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from shared.embeddings import get_embedder  # noqa: E402

LLM_COST_USD = 0.000304     # M9.1 baseline: gpt-oss-20b per request
LLM_LATENCY_S = 1.40        # M9.1 baseline (without WhatsApp network)
CACHE_LATENCY_S = {"exact": 0.002, "semantic": 0.06}   # semantic = embedding + search

# ==========================================================================
# Simulated traffic: query -> intent label (label sirf GRADING ke liye; cache ko nahi pata)
# ==========================================================================

ANSWERS = {
    "return_policy": "Returns 7 din ke andar, unused aur original box ke saath.",
    "delivery_lahore": "Lahore mein 1-2 working days.",
    "delivery_other": "Lahore ke bahar 3-5 working days.",
    "warranty": "Movement par 6 months warranty; strap/glass covered nahi.",
    "price_tw2041": "TW-2041 Ravi Chrono: Rs 8,499.",
    "price_tw2047": "TW-2047 Ravi Classic: Rs 5,999.",
    "cod": "Sirf Cash on Delivery.",
}

QUERIES = [
    ("What is your return policy?", "return_policy"),
    ("what is your return policy", "return_policy"),
    ("  What is your RETURN policy?? ", "return_policy"),
    ("What's your return policy?", "return_policy"),
    ("Can I return my watch?", "return_policy"),
    ("return policy kya hai", "return_policy"),
    ("How long does delivery take in Lahore?", "delivery_lahore"),
    ("how long does delivery take in lahore", "delivery_lahore"),
    ("Delivery time for Lahore?", "delivery_lahore"),
    ("How long does delivery take in Karachi?", "delivery_other"),   # Lahore jaisa, jawab ALAG
    ("How long does delivery take in Multan?", "delivery_other"),
    ("Is there warranty on the watch?", "warranty"),
    ("Is there a warranty on watches?", "warranty"),
    ("What is the price of TW-2041?", "price_tw2041"),
    ("What is the price of TW-2047?", "price_tw2047"),               # sirf 1 character ka farq!
    ("Do you accept card payment?", "cod"),
    ("Do you accept credit cards?", "cod"),
    # Personalized: KABHI cache nahi
    ("Where is my order #12345?", "order"),
    ("Where is my order #67890?", "order"),
]
WEIGHTS = [8, 5, 2, 3, 3, 2, 6, 3, 2, 3, 2, 4, 2, 3, 3, 3, 2, 3, 3]   # popular sawal zyada aate hain


def make_traffic(n: int = 60, seed: int = 7) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    return rng.choices(QUERIES, weights=WEIGHTS, k=n)


# ==========================================================================
# Layer 0: cacheability policy
# ==========================================================================

PERSONAL_RE = re.compile(r"(#\d{3,}|\border\b.*\d{3,}|\b03\d{9}\b|@\w+\.\w+)", re.I)


def is_cacheable(query: str) -> tuple[bool, str]:
    if PERSONAL_RE.search(query):
        return False, "personal/order-specific"
    return True, "ok"


# ==========================================================================
# Entity guard: semantic match tabhi valid jab "important entities" same hon
# ==========================================================================

CITIES = {"lahore", "karachi", "islamabad", "multan", "faisalabad", "rawalpindi", "peshawar"}
ENTITY_RE = re.compile(r"\b[a-z]{2}-\d{3,}\b|\b\d+\b")


def entities(query: str) -> frozenset[str]:
    q = query.lower()
    found = set(ENTITY_RE.findall(q))
    found |= {w for w in re.findall(r"[a-z]+", q) if w in CITIES}
    return frozenset(found)


def normalize(query: str) -> str:
    q = query.lower().strip()
    q = re.sub(r"[^\w\s#-]", "", q)        # punctuation hatao
    return re.sub(r"\s+", " ", q)


# ==========================================================================
# The layered cache
# ==========================================================================


@dataclass
class CacheConfig:
    model: str = "groq/openai/gpt-oss-20b"
    prompt_version: str = "support-v3"
    kb_version: int = 1
    ttl_s: int = 24 * 3600
    sem_threshold: float = 0.90
    entity_guard: bool = True


@dataclass
class SemEntry:
    vec: np.ndarray
    answer: str
    query: str
    ents: frozenset
    kb_version: int
    prompt_version: str
    created: float


class LayeredCache:
    def __init__(self, cfg: CacheConfig, embedder, cache_dir: str) -> None:
        self.cfg, self.embedder = cfg, embedder
        self.exact = diskcache.Cache(cache_dir)          # production: Redis
        self.sem: list[SemEntry] = []                    # production: Redis vector / Qdrant / pgvector

    def exact_key(self, query: str) -> str:
        """Key mein WO SAB kuch jo jawab badal sakta hai. Kuch bhool gaye = stale/galat jawab."""
        raw = "|".join([normalize(query), self.cfg.model, self.cfg.prompt_version,
                        f"kb{self.cfg.kb_version}"])
        return hashlib.sha256(raw.encode()).hexdigest()

    def lookup(self, query: str) -> tuple[str | None, str, float, str | None]:
        """returns (answer, layer, similarity, matched_query)"""
        ok, _ = is_cacheable(query)
        if not ok:
            return None, "bypass", 0.0, None
        hit = self.exact.get(self.exact_key(query))
        if hit is not None:
            return hit, "exact", 1.0, query
        if not self.sem:
            return None, "miss", 0.0, None
        qv = self.embedder([query])[0]
        q_ents = entities(query)
        now = time.time()
        best, best_sim = None, -1.0
        for e in self.sem:
            if (e.kb_version != self.cfg.kb_version or e.prompt_version != self.cfg.prompt_version
                    or now - e.created > self.cfg.ttl_s):
                continue                                  # stale -> ignore (invalidation)
            if self.cfg.entity_guard and e.ents != q_ents:
                continue                                  # TW-2041 vs TW-2047, Lahore vs Karachi
            sim = float(np.dot(qv, e.vec))
            if sim > best_sim:
                best, best_sim = e, sim
        if best is not None and best_sim >= self.cfg.sem_threshold:
            return best.answer, "semantic", best_sim, best.query
        return None, "miss", best_sim, None

    def store(self, query: str, answer: str) -> None:
        if not is_cacheable(query)[0]:
            return
        self.exact.set(self.exact_key(query), answer, expire=self.cfg.ttl_s)
        self.sem.append(SemEntry(self.embedder([query])[0], answer, query, entities(query),
                                 self.cfg.kb_version, self.cfg.prompt_version, time.time()))

    def bump_kb_version(self) -> None:
        """Knowledge update hua -> version badlo. Purani entries khud-ba-khud miss ho jayengi."""
        self.cfg.kb_version += 1


def fake_llm(intent: str) -> str:
    return ANSWERS.get(intent, "Aap ka order check karke batata hoon.")


# ==========================================================================
# Experiments
# ==========================================================================


@dataclass
class Stats:
    n: int = 0
    exact: int = 0
    semantic: int = 0
    miss: int = 0
    bypass: int = 0
    wrong: int = 0
    latency: float = 0.0
    cost: float = 0.0


def simulate(cache: LayeredCache, traffic, verbose_wrong: bool = True) -> Stats:
    st = Stats()
    label_of_answer = {v: k for k, v in ANSWERS.items()}
    shown: set[tuple[str, str]] = set()
    for query, intent in traffic:
        st.n += 1
        ans, layer, sim, matched = cache.lookup(query)
        if layer in ("exact", "semantic"):
            setattr(st, layer, getattr(st, layer) + 1)
            st.latency += CACHE_LATENCY_S[layer]
            if label_of_answer.get(ans) != intent:     # grading: galat cached jawab?
                st.wrong += 1
                if verbose_wrong and (query, matched) not in shown:
                    shown.add((query, matched))
                    print(f"    ❌ WRONG HIT ({layer}, sim={sim:.2f}): {query!r}\n"
                          f"       matched {matched!r} -> {ans!r}")
        else:
            st.miss += layer == "miss"
            st.bypass += layer == "bypass"
            st.latency += LLM_LATENCY_S
            st.cost += LLM_COST_USD
            cache.store(query, fake_llm(intent))
    return st


def print_stats(title: str, st: Stats) -> None:
    hits = st.exact + st.semantic
    base_cost, base_lat = st.n * LLM_COST_USD, st.n * LLM_LATENCY_S
    print(f"  {title}")
    print(f"    requests {st.n} | exact {st.exact} | semantic {st.semantic} | miss {st.miss} "
          f"| bypass {st.bypass} | hit rate {hits / st.n:.0%} | WRONG hits {st.wrong}")
    print(f"    cost ${st.cost:.5f} vs no-cache ${base_cost:.5f}  (saved {1 - st.cost / base_cost:.0%})"
          f" | avg latency {st.latency / st.n:.2f}s vs {base_lat / st.n:.2f}s")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--offline", action="store_true")
    args = p.parse_args()
    embedder = get_embedder("offline" if args.offline else "ollama")
    traffic = make_traffic()
    tmp = tempfile.mkdtemp(prefix="cache_lab_")
    opened: list[LayeredCache] = []

    def fresh(**kw) -> LayeredCache:
        d = tempfile.mkdtemp(dir=tmp)
        c = LayeredCache(CacheConfig(**kw), embedder, d)
        opened.append(c)
        return c

    try:
        print("\n=== EXP 1: Sirf EXACT cache (normalized) ===")
        st = simulate(fresh(sem_threshold=2.0), traffic)        # threshold > 1 = semantic off
        print_stats("exact only", st)

        print("\n=== EXP 2: Exact + SEMANTIC, entity guard OFF (khatarnaak) ===")
        thr = 0.80 if args.offline else 0.85
        st = simulate(fresh(sem_threshold=thr, entity_guard=False), traffic)
        print_stats(f"semantic thr={thr}, no guard", st)

        print("\n=== EXP 3: Exact + SEMANTIC, entity guard ON ===")
        st = simulate(fresh(sem_threshold=thr, entity_guard=True), traffic)
        print_stats(f"semantic thr={thr}, guard", st)

        print("\n=== EXP 4: Threshold sweep (guard OFF, taake trade-off saaf dikhe) ===")
        print(f"    {'threshold':>9} {'hit rate':>9} {'wrong hits':>11}")
        for t in (0.60, 0.70, 0.80, 0.85, 0.90, 0.95):
            s = simulate(fresh(sem_threshold=t, entity_guard=False), traffic, verbose_wrong=False)
            print(f"    {t:>9.2f} {(s.exact + s.semantic) / s.n:>9.0%} {s.wrong:>11}")
        print("    Threshold kam -> hit rate zyada, lekin GALAT jawab bhi zyada. Apne data par tune karo.")

        print("\n=== EXP 5: Invalidation (return policy 7 -> 14 din ho gayi) ===")
        c = fresh(sem_threshold=thr)
        c.store("What is your return policy?", ANSWERS["return_policy"])
        print(f"    before update: {c.lookup('What is your return policy?')[1]}")
        c.bump_kb_version()
        print(f"    after kb_version bump: {c.lookup('What is your return policy?')[1]}"
              f"  <- purana jawab serve nahi hua")

        print("\n=== EXP 6: Provider prompt caching (prefix caching) math ===")
        static, dynamic, n = 2300, 550, 30_000          # tokens; requests/month
        full, cached_price = 0.075, 0.0375              # $/M (Groq gpt-oss-20b, 50% cached discount)
        no_cache = (static + dynamic) * n * full / 1e6
        with_cache = (static * cached_price + dynamic * full) * n / 1e6
        print(f"    Prompt: {static} static tokens (system+FAQ) PEHLE, {dynamic} dynamic (history+user) BAAD mein")
        print(f"    Input cost/month: ${no_cache:.2f} -> ${with_cache:.2f} "
              f"(~{1 - with_cache / no_cache:.0%} input saving), TTFT bhi kam")
        print("    Shart: static hissa BILKUL same aur prompt ke SHURU mein ho. Beech mein timestamp")
        print("    ya user ka naam daal diya to cache toot jayega.")
        print(f"\n  Embedder: {embedder.name}")
    finally:
        for c in opened:            # Windows par open files delete nahi hoti, pehle close
            c.exact.close()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
