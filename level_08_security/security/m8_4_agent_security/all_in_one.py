"""
================================================================================
 M8.4  AGENT SECURITY (code-level)  --  SAB KUCH EK FILE MEIN
================================================================================

Yeh file 4 purani files (authz.py + limits.py + sql_guard.py + sandbox.py) ko
ek jagah jama kar deti hai, isi tarteeb mein:

    HISSA 1  -> ATTACK      : model ke proposed bure tool-calls (BOLA order,
                              bara refund, exfil email, unsafe SQL, untrusted code)
    HISSA 2  -> PROTECTION  : code-level checks jo model ki baat nahi maante --
                              (a) authz   = ownership + email allow-list + refund/approval
                              (b) limits  = step / time budget (runaway agent rokna)
                              (c) sql     = model ka SQL sirf safe read-only SELECT
                              (d) sandbox = model ka code band container mein
    HISSA 3  -> RUN         : attacker ke proposals ko guarded functions par chala
                              kar ALLOW/DENY dikhana (bina model/Ollama ke chalta hai)

ASAL NUKTA (roadmap): model ka tool-choice sirf ek PROPOSAL hai. Nateeja aam code
decide karta hai jisse model behes nahi kar sakta. Pehchaan (kaun logged-in hai)
model ke BAHAR se aati hai, prompt se nahi.

`app/` ko haath nahi lagaya. Yeh file usay sirf import karti hai.

--------------------------------------------------------------------------------
 CHALANA (Windows PowerShell) -- yeh commands AAP apne terminal mein chalayein:
--------------------------------------------------------------------------------
    cd C:\\Users\\abubakar\\Desktop\\security
    .venv\\Scripts\\activate
    python -m m8_4_agent_security.all_in_one          # saara demo (model nahi chahiye)

    # sql_guard ke liye: pip install sqlglot   (na ho to woh hissa skip ho jata hai)
================================================================================
"""
from __future__ import annotations

import json
import shlex
import time
from dataclasses import dataclass

from langchain_core.tools import tool

from app.config import DATA_DIR, OUTPUT_DIR
from app.tools import _append_jsonl, OUTBOX_FILE, REFUNDS_FILE


# =============================================================================
#  HISSA 1 : ATTACK  (model ke proposed bure tool-calls, DATA ki tarah)
# =============================================================================
#
# Attacker logged-in customer Ali Raza (cust_001) hai. Yeh woh tool-calls hain
# jo ek injected/jailbroken model propose kar sakta hai. HISSA 3 inhe guarded
# functions par chala kar dikhata hai ke code inhe rok deta hai.

# get_order attacks: (order_id, kya yeh deny hona chahiye?)
ORDER_ATTACKS = [
    ("ORD-1001", False),   # apna order -> milna chahiye (allow)
    ("ORD-2001", True),    # Sara (cust_002) ka order -> BOLA, deny
    ("ORD-9999", True),    # mojood hi nahi -> deny (aur same message, taake pata na chale)
]

# issue_refund attacks: (order_id, amount_pkr, kya deny/queue hona chahiye?)
REFUND_ATTACKS = [
    ("ORD-1001", 2000, False),    # apna order, chhota amount -> allow
    ("ORD-1001", 50000, True),    # paid (8750) se zyada + limit se upar -> deny/queue
    ("ORD-2001", 1000, True),     # Sara ka order -> deny (ownership)
]

# send_email attacks: (to, kya deny hona chahiye?)
EMAIL_ATTACKS = [
    ("ali.raza@example.com", False),        # apna address -> allow
    ("attacker@evil.example", True),        # bahar ka address -> exfiltration, deny
]

# Unsafe SQL (agar model kabhi SQL banaye): (sql, kya deny hona chahiye?)
SQL_ATTACKS = [
    ("SELECT status FROM orders WHERE order_id = 'ORD-1001'", False),  # safe read-only
    ("SELECT * FROM orders; DROP TABLE orders;", True),                # stacked + drop
    ("DELETE FROM orders", True),                                      # write
    ("SELECT * FROM internal_secrets", True),                          # table allow-list se bahar
]

# Untrusted code jo model bana sakta hai (sandbox mein chalega, seedha nahi).
UNTRUSTED_CODE = "import os; print(os.listdir('/'))"


# =============================================================================
#  HISSA 2 : PROTECTION  (code-level checks)
# =============================================================================

# -----------------------------------------------------------------------------
#  (a) authz -- ownership + email allow-list + refund limit/approval
#      (S1 / S2 / S6 ka ASLI fix)
# -----------------------------------------------------------------------------
ORDERS_FILE = DATA_DIR / "orders.json"

REFUND_AUTO_LIMIT_PKR = 5000   # is se upar -> insaani approval chahiye
APPROVAL_QUEUE = OUTPUT_DIR / "approval_queue.jsonl"


@dataclass(frozen=True)
class Session:
    """Pehchaan model ke BAHAR se. Model isay chhu nahi sakta."""
    customer_id: str
    name: str
    email: str


def _load_orders() -> dict:
    return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))


class ToolDenied(Exception):
    """Jab koi kaam mana ho. Caller isay safe message bana deta hai."""


def owns_order(session: Session, order: dict) -> bool:
    return order.get("customer_id") == session.customer_id


def lookup_order(session: Session, order_id: str) -> dict:
    """Order sirf tab do jab woh isi session ke customer ka ho."""
    order = _load_orders().get(order_id.strip().upper())
    if not order:
        raise ToolDenied(f"No order found with id {order_id}.")
    if not owns_order(session, order):
        # Yeh na batao ke order kisi aur ka mojood hai -> same message.
        raise ToolDenied(f"No order found with id {order_id}.")
    return order


def guarded_send_email(session: Session, to: str, subject: str, body: str) -> str:
    if to.strip().lower() != session.email.lower():
        raise ToolDenied(f"Email can only go to your own registered address ({session.email}).")
    _append_jsonl(OUTBOX_FILE, {"to": to, "subject": subject, "body": body})
    return f"Email sent to {to}."


def guarded_issue_refund(session: Session, order_id: str, amount_pkr: int) -> str:
    order = lookup_order(session, order_id)  # ownership yahin check hota hai (reuse)
    paid = int(order["total_pkr"])
    if amount_pkr <= 0:
        raise ToolDenied("Refund amount must be positive.")
    if amount_pkr > paid:
        raise ToolDenied(f"Refund cannot exceed what was paid (PKR {paid}).")
    if amount_pkr > REFUND_AUTO_LIMIT_PKR:
        # Bara + irreversible -> karne ke bajaye insaan ke liye queue (approval gate)
        _append_jsonl(APPROVAL_QUEUE, {
            "type": "refund", "order_id": order_id, "amount_pkr": amount_pkr,
            "customer_id": session.customer_id, "status": "pending_human_approval",
        })
        return (f"Your refund of PKR {amount_pkr} needs manager approval and has been "
                f"queued. A human will review it shortly.")
    _append_jsonl(REFUNDS_FILE, {"order_id": order_id, "amount_pkr": amount_pkr})
    return f"Refund of PKR {amount_pkr} issued for {order_id}."


def make_tools(session: Session, search_tool) -> list:
    """session ko closure mein 'band' kar ke LangChain tools banata hai -- model
    pehchaan khud handle nahi karta. search_tool bahar se aata hai (M8.5 wala),
    taake yeh module sirf authorization par focus rahe. (M8.9 ise use karta hai.)"""

    @tool
    def get_order(order_id: str) -> str:
        """Look up ONE of your own orders by its ID (e.g. ORD-1001)."""
        try:
            return json.dumps(lookup_order(session, order_id), ensure_ascii=False)
        except ToolDenied as e:
            return str(e)

    @tool
    def send_email(to: str, subject: str, body: str) -> str:
        """Email a copy of information to your own registered email address."""
        try:
            return guarded_send_email(session, to, subject, body)
        except ToolDenied as e:
            return f"BLOCKED: {e}"

    @tool
    def issue_refund(order_id: str, amount_pkr: int) -> str:
        """Request a refund on one of your own orders."""
        try:
            return guarded_issue_refund(session, order_id, amount_pkr)
        except ToolDenied as e:
            return f"BLOCKED: {e}"

    return [search_tool, get_order, send_email, issue_refund]


# -----------------------------------------------------------------------------
#  (b) limits -- runaway agent rokna (step / time / cost)
# -----------------------------------------------------------------------------
# Tool-loop mein phansa agent paisa jalata hai aur attack ho sakta hai (S8).
MAX_STEPS = 8            # LangGraph recursion_limit
WALL_CLOCK_SECONDS = 60  # ek turn ki hard deadline


class LimitExceeded(Exception):
    pass


@dataclass
class RunBudget:
    max_steps: int = MAX_STEPS
    deadline_s: float = WALL_CLOCK_SECONDS
    _start: float = 0.0

    def start(self) -> "RunBudget":
        self._start = time.monotonic()
        return self

    def check_time(self) -> None:
        if self._start and (time.monotonic() - self._start) > self.deadline_s:
            raise LimitExceeded(f"Turn exceeded {self.deadline_s}s deadline.")

    @property
    def config(self) -> dict:
        """agent.invoke(..., config=budget.config) ko dena -> steps cap."""
        return {"recursion_limit": self.max_steps}


# -----------------------------------------------------------------------------
#  (c) sql_guard -- model ka SQL bina-bharose; sirf single read-only SELECT
# -----------------------------------------------------------------------------
ALLOWED_TABLES = {"orders", "products"}
BANNED = {"insert", "update", "delete", "drop", "alter", "create", "truncate",
          "grant", "revoke", "attach", "pragma", "exec", "execute"}


class UnsafeSQL(Exception):
    pass


def validate_select(sql: str, allowed_tables: set[str] = ALLOWED_TABLES) -> str:
    """SQL wapas karo agar woh safe single read-only SELECT hai, warna raise."""
    try:
        # sqlglot: SQL ko string nahi, proper "parse" karta hai (SELECT, table, WHERE
        #          tukron mein tor kar) -> pakka check ho sakta hai ke read-only SELECT hai.
        import sqlglot
        from sqlglot import exp
    except ImportError as e:
        raise UnsafeSQL("sqlglot not installed. Run: pip install sqlglot") from e

    statements = [s for s in sqlglot.parse(sql, read="sqlite") if s]
    if len(statements) != 1:
        raise UnsafeSQL("Only a single statement is allowed (no stacked queries).")

    stmt = statements[0]
    if not isinstance(stmt, exp.Select):
        raise UnsafeSQL("Only SELECT statements are allowed.")

    lowered = sql.lower()
    for word in BANNED:
        if word in lowered:
            raise UnsafeSQL(f"Banned keyword in query: {word}")

    tables = {t.name.lower() for t in stmt.find_all(exp.Table)}
    bad = tables - allowed_tables
    if bad:
        raise UnsafeSQL(f"Query touches tables that are not allowed: {sorted(bad)}")

    return sql


# -----------------------------------------------------------------------------
#  (d) sandbox -- model ka code apni machine par nahi, band container mein
# -----------------------------------------------------------------------------
# Har flag ek khaas escape/abuse raasta band karta hai.
HARDENING = [
    "--network", "none",          # koi exfiltration / callback nahi
    "--read-only",                # filesystem read-only
    "--tmpfs", "/tmp:size=16m",   # sirf chhoti scratch space
    "--memory", "256m",           # memory cap
    "--cpus", "0.5",              # CPU cap
    "--pids-limit", "64",         # fork bomb nahi
    "--user", "65534:65534",      # 'nobody' ban kar chale, root nahi
    "--cap-drop", "ALL",          # saari Linux capabilities drop
    "--security-opt", "no-new-privileges",
]


def build_docker_command(code: str, image: str = "python:3.12-slim", timeout_s: int = 10) -> str:
    """Ek `docker run` command banata hai jo `code` ko safely chalaye. Khud chalata
    nahi -- aap print ki hui command khud run karte hain (Docker Desktop chahiye)."""
    inner = f"timeout {timeout_s} python -"
    flags = " ".join(HARDENING)
    return f"echo {shlex.quote(code)} | docker run --rm -i {flags} {image} {inner}"


# =============================================================================
#  HISSA 3 : RUN  (attacker proposals ko guarded functions par chalana)
# =============================================================================
# Yeh model nahi chalata -- seedha guarded functions ko attacker ke arguments se
# call karta hai, taake saaf dikhe ke code-level check inhe rokta hai.

def _ok(expected_deny: bool, denied: bool) -> str:
    return "(OK)" if expected_deny == denied else "(WRONG)"


def main() -> None:
    # Logged-in customer = Ali Raza (pehchaan code deta hai, model nahi)
    session = Session(customer_id="cust_001", name="Ali Raza", email="ali.raza@example.com")
    print(f"\nLogged-in: {session.name} ({session.customer_id})\n" + "=" * 70)

    # ---- (a) ownership check: get_order ----
    print("\n[authz] get_order (ownership / BOLA):")
    for order_id, should_deny in ORDER_ATTACKS:
        try:
            order = lookup_order(session, order_id)
            print(f"  ALLOW {_ok(should_deny, False)} | {order_id} -> {order['customer_name']}")
        except ToolDenied as e:
            print(f"  DENY  {_ok(should_deny, True)} | {order_id} -> {e}")

    # ---- (a) refund limit + approval ----
    print("\n[authz] issue_refund (ownership + limit + approval):")
    for order_id, amount, should_deny in REFUND_ATTACKS:
        try:
            msg = guarded_issue_refund(session, order_id, amount)
            # bara refund hua nahi -> approval queue mein gaya (yani asar mein "roka gaya")
            queued = "needs manager approval" in msg.lower()
            tag = "QUEUE" if queued else "ALLOW"
            print(f"  {tag:5} {_ok(should_deny, queued)} | {order_id} PKR {amount} -> {msg}")
        except ToolDenied as e:
            print(f"  DENY  {_ok(should_deny, True)} | {order_id} PKR {amount} -> {e}")

    # ---- (a) email allow-list ----
    print("\n[authz] send_email (recipient allow-list / exfiltration):")
    for to, should_deny in EMAIL_ATTACKS:
        try:
            msg = guarded_send_email(session, to, "Your order", "details...")
            print(f"  ALLOW {_ok(should_deny, False)} | {to} -> {msg}")
        except ToolDenied as e:
            print(f"  DENY  {_ok(should_deny, True)} | {to} -> {e}")

    # ---- (b) limits ----
    print("\n[limits] run budget:")
    budget = RunBudget().start()
    print(f"  max_steps={budget.max_steps} (recursion_limit), deadline={budget.deadline_s}s")
    print(f"  invoke config -> {budget.config}")

    # ---- (c) sql_guard ----
    print("\n[sql_guard] model-generated SQL (sirf safe SELECT):")
    for sql, should_deny in SQL_ATTACKS:
        try:
            validate_select(sql)
            print(f"  ALLOW {_ok(should_deny, False)} | {sql}")
        except UnsafeSQL as e:
            print(f"  DENY  {_ok(should_deny, True)} | {sql}  ->  {e}")

    # ---- (d) sandbox ----
    print("\n[sandbox] untrusted code -> safe docker command (print only):")
    print("  " + build_docker_command(UNTRUSTED_CODE))

    print("\n" + "=" * 70)
    print("Note: ownership + refund limit + email allow-list waqai rokte hain.")
    print("Step limit (recursion_limit) lagta hai; time limit (check_time) m8_9 mein")
    print("call nahi hota -- yeh file sirf dikhati hai ke woh kahan lagna chahiye.\n")


if __name__ == "__main__":
    main()
