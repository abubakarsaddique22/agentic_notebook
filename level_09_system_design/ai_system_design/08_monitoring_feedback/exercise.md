# M9.8 · Exercise

## Part A: Code
1. `monitoring_lab.py` chalao. Report padh kar (code dekhe bina) likho: kya hua, kab, kis version mein, kis intent par?
2. `simulate()` mein ek nayi problem daalo: din 12 se `warranty` ka bad-rate 40% (KB update mein warranty doc galti se delete). Kya alerts ne pakda? Step 3b ne?
3. `alerts()` mein ek naya alert: kisi ek intent ka bad-rate 7-day baseline se 2x ho jaye (intent-level alert). Kya ye day 8 par delivery regression ko overall alert se pehle/behtar pakadta hai?
4. `traces.db` ko DB Browser for SQLite mein kholo aur SQL likho: "har din ka fallback traffic % aur us ka implicit bad-rate".
5. `label_me.csv` Excel mein kholo, 5 rows ka `expected_output` bharo. Phir socho: ye Level 7 ke DeepEval test mein kaise jayenge?
6. **Bonus:** Langfuse free account banao aur `langfuse_tracing.py` chalao. UI mein trace ka waterfall aur score dekho.

## Part B: Design
Apne WhatsApp bot ke liye likho:
1. Trace record ke fields (kam se kam 15)
2. 3 explicit aur 4 implicit feedback signals, aur WhatsApp par kaise capture honge
3. 5 alerts (threshold ke saath) aur har ek ka runbook (1–2 lines)
4. Client ke liye monthly report ke 6 numbers
