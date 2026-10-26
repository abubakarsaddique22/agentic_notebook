"""LLM client. Asal mein yahan AsyncOpenAI / AsyncAnthropic client hoga."""
import asyncio


class FakeLLM:
    async def complete(self, message: str, history: list[dict]) -> str:
        await asyncio.sleep(0.5)                 # network + model ka waqt
        return f"(LLM) Aap ka sawal: '{message}'. Main madad ke liye haazir hoon."

    async def stream(self, message: str):
        for word in f"(LLM) {message} ka jawab".split():
            await asyncio.sleep(0.05)
            yield word
