# Class 8 — MCP Security + Human Approval (Roman Urdu)

## Goal
Class 7 ka Travel (8001), Policy RAG (8002), Work (8003) unchanged; **naya protected Booking MCP (8004)** add hua hai. Agent sirf pehle 3 servers ke safe/demo tools use karta hai. Booking tools model ko expose **nahi** kiye gaye.

## Concepts

- **Authentication (401)**: Caller ka bearer token verify hota hai. Token nahi / invalid -> reject.
- **Authorization (403 or tool error)**: Valid token bhi har operation nahi kar sakta. Traveler ka scope `booking:read`; admin ka `booking:approve` aur `booking:execute`.
- **Human-in-the-loop**: Host pe `APPROVE` typed input ke baad admin scope se server-side request state update hoti hai. LLM kabhi approval nahi deta.
- **Tool restrictions**: `agent.py` ke adapter config mein Booking server bilkul nahi hai. Lekin **only hiding tool enough nahi**; booking server apne aap authorization aur approval check karta hai.
- **Approval state**: SQLite mein persisted, 15-minute expiry, random request IDs; only `approved` status se exactly once demo booking execute.
- **No real bookings**: `DEMO-...` ID aur `real_booking: false` aata hai. Koi vendor API, payment, refund ya reservation nahi.

### Security boundary

```text
Travel MCP (:8001) ─┐
Policy RAG (:8002) ─┼── MCPAdapter ── Groq LangChain Agent (read/demo tools)
Work MCP (:8003) ───┘

Host CLI -- explicit user input -- Authenticated MCP Client ── Booking MCP (:8004)
                                                             ├── 401: token verification
                                                             ├── authorization per operation
                                                             ├── pending -> approved/rejected
                                                             └── approved -> executed (exactly once)
```

## Files

- `servers/travel_server.py` — unchanged from Class 7
- `servers/policy_server.py` — unchanged Class 7 semantic RAG
- `servers/work_server.py` — unchanged Class 7 task demo
- `servers/booking_server.py` — **new** authentication + authorization + SQLite approval workflow
- `booking_client.py` — `httpx2` bearer-auth transport for MCP SDK v2
- `approval_workflow.py` — interactive request/approve/execute flow
- `test_security.py` — reject missing auth and deny unauthorized execution
- `agent.py` — only 3 permitted servers; Booking tool unavailable to model
- `build_index.py`, `rag_utils.py`, `test_rag.py` — Class 7 RAG files
- `start_servers.py` — original 3-server launcher; start booking server separately

## Installation — Windows PowerShell

```powershell
cd MCP_Practical
.venv\Scripts\Activate.ps1
cd class_08
python -m pip install -r requirements.txt
```

Root `MCP_Practical/.env` should contain:

```dotenv
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_gemini_key
BOOKING_USER_TOKEN=generate_long_random_secret_1
BOOKING_ADMIN_TOKEN=generate_long_random_secret_2
```

Generate strong random tokens locally:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32)); print(secrets.token_urlsafe(32))"
```

**Never commit `.env` to Git.** Both demo roles are configured in one host environment to simplify training. In production, keep admin credentials with a *separate* authenticated approver, not with agent/user process. `https://auth.example.com` in `booking_server.py` is a **placeholder issuer**, not a real authorization server; this demo uses static tokens. Replace with real OAuth 2.1 IdP, JWT verification and managed identity before deployment.

## Run order (4 terminals)

If Class 7 servers occupy ports 8001–8003, stop them first.

Terminal 1, class_08 root:

```powershell
python start_servers.py
```

This launches the unchanged Travel, Policy and Work MCP servers. Or run those three scripts in separate terminals.

Terminal 2:

```powershell
python servers/booking_server.py
```

Terminal 3 (RAG must have prebuilt index):

```powershell
python build_index.py
python agent.py
```

Terminal 4:

```powershell
python test_security.py
python approval_workflow.py
```

`approval_workflow.py` asks for city, nights, `APPROVE` or rejection, and finally `EXECUTE`. Outputs a **demo** ID only.

## Expected tests

1. Unauthenticated POST `/mcp` -> **401**.
2. Traveler token can create/read its own booking request; trying `execute_approved_booking` -> tool error / forbidden.
3. Admin can approve or reject a pending request, but cannot execute a pending/unapproved/rejected request.
4. Approved, not expired request -> one demo execution. Second attempt -> rejected.
5. Request expires after 15 minutes; execution rejected.
6. LLM tool list does not include booking server tools.

## Important caveats

- Static bearer tokens and CLI confirmation are **learning scaffolding**; do not deploy as a real booking approval solution.
- Admin token being available to the CLI user means it is *not independent user authentication*. Production requires distinct approver sign-in, audit log, CSRF controls where applicable, and stronger controls for approval identity.
- Only Booking MCP is bearer-protected in this class. Original 3 HTTP MCP servers are **local development only**, not securely exposed externally.
- For production, protect all HTTP MCP services, use HTTPS/TLS, rotate credentials, log safely, restrict egress and implement vendor booking reconciliation.
- Stored approval state is protected by SQLite transactions; production would use a real DB, proper migrations, roles and audit event storage.
- On MCP SDK v2, `httpx2.AsyncClient` plus `streamable_http_client(url,http_client=...)` is used to send Authorization headers. Do not pass `headers=` directly to `streamable_http_client`.

## Practice

1. `test_security.py` se check karo ke bina token 401 milta hai.
2. Traveler ke credentials se approve tool call karke deny verify karo.
3. Approval ko reject karo, phir execute attempt try karo.
4. Ek approval execute karke repeat karo; second time fail hona chahiye.
5. `agent.py` mein list tools check karo: booking tools absent.

## Docs
- https://py.sdk.modelcontextprotocol.io/run/authorization/
- https://py.sdk.modelcontextprotocol.io/client/transports/
- https://modelcontextprotocol.io/specification/
