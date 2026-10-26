# Langfuse UI Features (bina code — lekin industry mein roz use hote hain)

cloud.langfuse.com par khud karke dekho. Har ek ke saath chhota exercise.

---

## 1. Dashboards
**Kahan:** left sidebar → **Dashboards**
**Kya:** Traces, latency, cost, tokens, scores — time ke saath charts. Environment, release, user, tags se filter.
Apne custom dashboards bhi bana sakte ho (widgets).

**Exercise:** Naya dashboard → widget: "Total cost by model", doosra: "Average user_rating score".

---

## 2. LLM-as-a-Judge Evaluators (production par automatic scoring)
**Kahan:** **Evaluators** (Evaluation section) → **+ Set up evaluator**
**Kya:** Folder 06 ke judges **offline** (dataset) the. Yeh **live traces/observations** par khud chalte hain.
- Ready-made templates: hallucination, helpfulness, toxicity, correctness, conciseness...
- Ya apna prompt likho (`{{input}}`, `{{output}}` variables map karo)
- Filter (e.g. sirf `support-answer` generations) + sampling (e.g. 10%)
- Pehle Settings → **LLM Connections** mein OpenAI key daalni hoti hai (judge model ke liye)

**Exercise:** Evaluator: "Is the reply in Roman Urdu? Score 1 or 0", sirf `production` environment, 20% sampling.

---

## 3. Annotation Queues (human review)
**Kahan:** **Annotation Queues** → New queue
**Kya:** Traces ki queue jahan team ek ek trace dekh kar scores deti hai. Pehle **Score Configs** banao
(Settings → Scores) — e.g. `correct` (boolean), `reason` (categorical: wrong_info / rude / off_topic).

**Exercise:** Queue "support-review" banao, traces list se 3 traces select → "Add to queue" → khud review karo.

---

## 4. Score Configs
**Kahan:** Project Settings → **Scores / Score Configs**
**Kya:** Score ka naam + type + allowed values fix karo (taake team consistent rahe). `create_score(config_id=...)`
se code bhi isi config ko follow karta hai.

---

## 5. Playground
**Kahan:** **Playground** (ya kisi generation par "Open in Playground")
**Kya:** Wahi messages ke saath prompt/model badal kar dobara chalao. Achha lage to **prompt save** karo (naya version).

**Exercise:** Kisi bure jawab wali generation ko playground mein kholo, system prompt improve karo, `watch-support` ka naya version save karo.

---

## 6. Datasets → Runs → Compare
**Kahan:** Datasets → dataset → **Runs** → 2+ select → Compare
**Kya:** Item-wise outputs + scores side-by-side. UI se bhi experiment chala sakte ho (prompt + dataset select karke).

---

## 7. Sessions & Users
- **Sessions:** poori conversation chat ki shakal mein, session-level scores
- **Users:** har user ki traces, total tokens, cost — "kaunsa customer sabse mehnga hai?"

---

## 8. Models & Prices
**Kahan:** Project Settings → **Models**
**Kya:** Cost calculation ke liye model prices. Apna/local model ho to custom price add karo (warna cost 0 dikhegi).

---

## 9. Trace par actions
- **Add to dataset** (trace → button)
- **Bookmark**, **comments** (team discussion)
- **Public share link** (debugging ke liye kisi ko dikhana)
