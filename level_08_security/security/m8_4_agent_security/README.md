# M8.4 - Agent & Tool Security

## Pehle concepts samajh lein

- **Agent**: ek LLM jo sirf jawab nahi deta balke tools call karke kaam bhi karta
  hai (order dekhna, email bhejna, refund dena).

- **Least privilege (sabse kam ikhtiyar)**: agent/tool ko sirf utni ijazat do
  jitni zaroori hai. Support bot ko DB delete karne ki ijazat nahi honi chahiye.

- **Read-only vs consequential actions**:
  - read-only = sirf parhna, nuqsan nahi (policy search, apna order dekhna).
  - consequential = asar paida karne wale (email bhejna, refund dena, data badalna,
    code chalana). Yeh zyada checking maangte hain.

- **Model output is untrusted**: model ka chuna hua tool aur arguments ek
  "tajweez" hain, hukm nahi. Asal faisla NORMAL code karta hai jise model baat
  karke nahi badal sakta. Yahi is module ka dil hai.

- **Authorization (ijazat check)**: tool chalane se pehle code check kare ke yeh
  banda is cheez ka haqdar hai bhi ya nahi.

- **BOLA (Broken Object Level Authorization)**: jab ownership check na ho to banda
  doosre ki cheez tak pohanch jaye (Ali, Sara ka order dekh le). Fix: code mein
  check "yeh order isi logged-in customer ka hai?".

- **Allow-list**: sirf pehle se manzoor shuda cheezein chalne dena (jaise email
  sirf customer ke apne address par).

- **Human approval / confirmation gate**: bara ya ulta na hone wala (irreversible)
  kaam khud na karo, insaan ki manzoori ke liye queue mein daal do.

- **Step / runtime / cost limits**: agent ko loop mein phasne se rokna (warna
  paisa aur waqt zaya, aur yeh khud ek attack ho sakta hai).

- **Sandboxing**: model ka likha code apne computer/ijazaton par mat chalao; ek
  band (isolated) container mein chalao jahan na network ho, na files likhi
  jayein, memory/CPU ki hadd ho. Model ka bana **SQL / commands / URLs** bhi
  bina-bharose samjho.

## Ek bari baat

Model ka tool call ek *request* hai. HONA ya na hona code decide karta hai. Hum
logged-in `Session` model ke BAHAR se dete hain, is liye pehchaan woh cheez nahi
jise prompt se badla ja sake.

| File | Theek karta hai | Kaam |
|------|------------------|------|
| `authz.py` | V2, V3, V4 / S1, S2, S6 | ownership check, email allow-list, refund cap + approval queue; session-bound tools banata hai |
| `limits.py` | V9 / S8 | step limit (recursion_limit), wall-clock deadline, token budget |
| `sql_guard.py` | generated SQL | sqlglot: sirf single read-only SELECT, allowed tables par |
| `sandbox.py` | generated code | band `docker run` banata hai (no net, read-only, caps, non-root) |

## Approval gate

PKR 5000 se zyada refund KHUD nahi hota. Woh `outputs/approval_queue.jsonl` mein
`pending_human_approval` ke saath chala jaata hai. Yahi "irreversible kaam ke liye
insaani manzoori" wala usool hai, saadi shakal mein.

## Chalana (Windows PowerShell)

```powershell
cd C:\Users\abubakar\Desktop\security
.venv\Scripts\activate
pip install sqlglot
python -m m8_4_agent_security.sql_guard      # SQL allow/deny dekhein
python -m m8_4_agent_security.sandbox        # ek hardened docker command chhapta hai
```

Docker Desktop sirf tab chahiye jab sandbox ka code waqai chalana ho. Baad mein
install karein; SQL aur authz ke liye kuch extra nahi chahiye.
