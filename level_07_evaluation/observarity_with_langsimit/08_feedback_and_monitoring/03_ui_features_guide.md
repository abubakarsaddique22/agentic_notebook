# LangSmith UI Features (code ke bina — lekin industry mein bohat use hote hain)

Yeh sab smith.langchain.com par khud karke dekho. Har ek ke saath ek chhota exercise hai.

---

## 1. Monitor tab (Dashboards)
**Kahan:** Tracing Project → **Monitor**
**Kya:** Trace count, latency (p50/p99), error rate, tokens, cost, feedback scores — time ke saath charts.
Metadata se group kar sakte ho (e.g. `prompt_version` wise latency).

**Exercise:** Apne project ka Monitor tab kholo, "Group by" metadata `user_id` karo.

---

## 2. Automation Rules
**Kahan:** Project → **+ Add Rule** (ya trace list par filter laga ke "Add rule")
**Kya:** Filter + sampling rate + action. Actions:
- **Add to dataset** — e.g. sab `user_rating = 0` runs automatically dataset mein
- **Add to annotation queue** — human review ke liye
- **Online evaluator** — LLM judge production traces par khud chale
- **Webhook** — apne server ko notify karo

**Exercise:** Rule banao: filter `feedback user_rating = 0` → action: Add to dataset `bad-replies`.

---

## 3. Online Evaluators
**Kya:** Folder 06 wale evaluators **offline** the (dataset par). Online evaluators **live production traces**
par chalte hain (sampling ke saath, e.g. 10%). Bina reference answer ke — e.g. "Is reply polite?",
"Did bot hallucinate?".

**Exercise:** Rule → Online evaluator → LLM-as-judge → prompt: "Is the reply in Roman Urdu? yes/no".

---

## 4. Annotation Queues (Human review)
**Kahan:** Left sidebar → **Annotation Queues**
**Kya:** Runs ki queue jahan team members ek ek run dekh kar score/correction dete hain.
Rubric (feedback keys) define karte ho. Reviewed runs → dataset.

**Exercise:** Queue banao "support-review", 3 runs add karo, khud review karo.

---

## 5. Alerts
**Kahan:** Project → **Alerts**
**Kya:** Error rate / latency / feedback score threshold cross ho to Slack/PagerDuty/webhook alert.

**Exercise:** Alert: error rate > 5% in 15 min.

---

## 6. Playground
**Kahan:** Kisi bhi LLM run par **"Playground"** button, ya Prompts → prompt → Playground
**Kya:** Wahi input ke saath prompt/model badal kar dobara chalao. Dataset par poora experiment bhi
UI se chal jata hai.

**Exercise:** Kisi bure jawab wale LLM run ko Playground mein kholo, system prompt improve karo.

---

## 7. Compare View (Experiments)
**Kahan:** Dataset → Experiments → 2+ select → **Compare**
**Kya:** Example-wise side-by-side outputs + scores, regressions laal/green.

---

## 8. Threads
**Kahan:** Project → **Threads** tab
**Kya:** `thread_id` / `session_id` metadata wale traces ek conversation ki shakal mein.
