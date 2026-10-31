"""
=====================================================================
 HELPER FILE: llm_setup.py   (ye file har class folder mein same copy hai)
=====================================================================
 CONCEPT: LLM Connection
 Kya hai : CrewAI ke har Agent ko ek "dimaag" (LLM) chahiye hota hai.
           Ye file .env se parhti hai ke aap kaunsa provider use kar
           rahe ho (Ollama ya Groq) aur ek LLM object bana ke de deti hai.
 Kyun    : Har file mein baar baar API key aur model likhne ki zaroorat
           nahi. Provider badalna ho to sirf .env mein ek line badlo.

 Providers:
   ollama (DEFAULT) -> model gpt-oss:20b-cloud
                       Ye "cloud" model hai: Ollama app aap ke PC pe
                       chalti hai, lekin model Ollama ke server pe chalta
                       hai (PC pe bara download nahi). Pehle ek dafa:
                           ollama signin
   groq             -> model openai/gpt-oss-120b (Groq ka latest GPT model)
                       Key: https://console.groq.com/keys

 Use kaise karein:
     from llm_setup import get_llm
     llm = get_llm()                    # default temperature 0.3
     llm = get_llm(temperature=0.0)     # zyada "seedha" jawab

 EMBEDDER:
     Memory aur Knowledge ko text ko numbers (vectors) mein badalna
     parta hai — isay "embedding" kehte hain. Hum "onnx" use kar rahe
     hain jo aapke PC pe locally chalta hai (free, koi key nahi).
     Pehli dafa chalane pe ~80MB model download hoga.
=====================================================================
"""

import os

from dotenv import load_dotenv
from crewai import LLM

load_dotenv()  # course root wali .env file parh lo

# Local, free embeddings (Memory + Knowledge ke liye)
EMBEDDER = {"provider": "onnx"}


def get_llm(temperature: float = 0.3) -> LLM:
    """.env ke LLM_PROVIDER ke hisaab se LLM object return karta hai."""
    provider = (os.getenv("LLM_PROVIDER") or "ollama").strip().lower()

    if provider == "ollama":
        # Ollama app chalu honi chahiye (system tray mein icon).
        return LLM(
            model="ollama/" + (os.getenv("OLLAMA_MODEL") or "gpt-oss:20b-cloud"),
            base_url=os.getenv("OLLAMA_URL") or "http://localhost:11434",
            temperature=temperature,
        )

    if provider == "groq":
        # Groq "OpenAI-compatible" API deta hai, isliye provider="openai"
        # aur base_url Groq ka diya hai.
        return LLM(
            model=os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b",
            provider="openai",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=temperature,
        )

    raise ValueError(
        f"LLM_PROVIDER='{provider}' samajh nahi aaya. "
        "ollama ya groq likho (.env file mein)."
    )
