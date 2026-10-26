# M9.7 · Exercise

## Part A: Code
1. `try_app.py` chalao. 6 sync cases mein se kitno mein LLM call hui? Har ek ka route aur latency note karo.
2. `components.py` mein `LLMIntentClassifier` likho (same `classify(text) -> str` interface), jo Groq se intent maange (JSON). Phir `RuleIntentClassifier` ko wrap karo: rules "unknown" dein tabhi LLM classifier chale. `app.py` mein sirf composition root badlo.
3. M9.2 ka hybrid retriever `Retriever` interface ke peeche lagao (`search(query, k) -> list[dict]`). Pipeline ka code badla?
4. `/webhook/whatsapp` mein ek check add karo: message 24 ghante se purana ho (timestamp field) to ignore.
5. **Bonus:** `run_report` ko fail karwao (exception) aur dekho `/jobs/{id}` mein `failed` aata hai. Phir retry ka endpoint banao.

## Part B: Decide
Har task ke liye: pattern (single call / chain / routing / parallel / orchestrator / evaluator / agent), execution mode (sync / async / job / workflow / batch), aur 1 line kyun:
1. Invoice PDF se fields nikaalna, 500 invoices roz
2. Customer support WhatsApp bot
3. "Hamare 5 competitors ki pricing research karke report do"
4. Blog post likhna, phir quality check, phir improve
5. Refund request jis mein owner ki approval chahiye (approval 2 din baad bhi aa sakti hai)

## Part C: Architecture diagram
Apne WhatsApp bot ka end-to-end flow diagram (section 2 jaisa) Mermaid mein banao, apne real components ke saath. Ye capstone mein use hoga.
