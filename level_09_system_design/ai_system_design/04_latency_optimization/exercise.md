# M9.4 · Exercise

## Part A: Code
1. `latency_lab.py --mock` aur real mode dono chalao. EXP 1 ka waterfall dekho: real Groq par LLM ka hissa kitna hai?
2. EXP 1 ko modify karo: retrieval aur dono tools `asyncio.gather` se parallel chalao. Total kitna bacha?
3. `MockLLM(tps=80)` karke (frontier jaisa slow model) EXP 5 dobara chalao. Output length ka asar kitna bara hua?
4. EXP 6 mein apne bot ke numbers daalo (peak QPS, latency, tokens) aur Groq console par apni limits se compare karo.

## Part B: Diagnose
Har case mein bottleneck aur pehla fix likho:
1. Web chatbot: TTFT 4s, total 5s. Input 30,000 tokens (poora PDF prompt mein).
2. WhatsApp bot: TTFT 0.3s, total 9s. Output avg 1,200 tokens (reasoning effort high).
3. Agent: 6 tool calls, har ek 0.8s, sab sequential. Total 7s.
4. Support bot: 4 LLM calls har message par (language detect → intent → answer → tone check).
5. Report generator: user ko 45s wait karna parta hai, aur woh page band kar deta hai.

## Part C: Latency budget
Ek voice bot (phone call) ka design hai. Target: user bolna band kare to 1s ke andar jawab shuru ho.
Components: speech-to-text, LLM, text-to-speech, network. Har ek ka budget likho, aur 3 design choices batao jo is budget ko possible banayein.
