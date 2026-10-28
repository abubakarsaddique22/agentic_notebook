# Class 09 — Production MCP Deployment + LLMOps (Roman Urdu)

> Yeh **deployment-ready learning baseline** hai, fully hardened production system nahin. Sab bookings **DEMO** hain. Real hotels, payments, flights aur work-service writes nahin hoti. `travel`/`work` Class 8 ke business logic se unchanged hain; container binding `0.0.0.0` ki hai.

## 1. Architecture

`Agent (Groq) → Docker DNS → Travel :8001, Policy RAG :8002, Work :8003`

`Approval CLI → Protected Booking MCP :8004 → SQLite volume` (agent ko iski URL/token/tool nahin milti).

`Monitor → MCP initialize + list_tools → Prometheus /metrics → Prometheus server`.

Services internal Docker network par hain; **koi MCP port host par published nahin**. Network egress Groq, Gemini aur Open-Meteo ke liye enabled hai. Authentication abhi sirf Booking server par hai; Travel/Policy/Work servers sirf internal trusted network ke liye suitable hain.

## 2. Dependencies

Docker Engine + Docker Compose v2, working internet; valid `GROQ_API_KEY`, `GOOGLE_API_KEY`. Python SDK v2: `mcp>=2,<3`. Host par Python install necessary nahin.

## 3. Step-by-step commands (PowerShell, class_09 folder mein)

```powershell
Copy-Item .env.example .env
# .env edit karo: GROQ_API_KEY / GOOGLE_API_KEY / 2 unique random tokens
python -c "import secrets; print(secrets.token_urlsafe(32))"
docker compose build
docker compose --profile tools run --rm indexer
docker compose up -d travel policy work booking monitor prometheus
docker compose ps
docker compose logs --tail=50 policy
# Agent is ONE-OFF CLI, daemon nahin:
docker compose --profile tools run --rm agent
# Human approval demo (interactive):
docker compose --profile tools run --rm approval
```

Agar policy document change ho: indexer dobara run karo; index volume persisted rahega. Policy filename aur SHA256 validation Class 7 jaisa hai.

## 4. Important files

| File | Kaam |
|---|---|
| Dockerfile | Python image, appuser UID 10001, required packages |
| compose.yaml | 4 services, agent/indexer/approval one-off jobs, metrics stack |
| healthcheck.py | Actual MCP initialize + tools discovery ka protocol check |
| healthcheck_booking.py | Authenticated booking handshake |
| json_logging.py | Structured JSON formatter for our monitor logs |
| monitor.py | 30-second interval MCP probe and Prometheus gauges/counters |
| prometheus.yml | Scrape monitor:9100 |
| build_index.py | Gemini embedding JSON index persistent Docker volume mein |
| servers/*.py | Earlier class business functions; host `0.0.0.0` |
| agent.py | Docker service-name MCP URLs, not localhost |

## 5. MCP URL conversion

Host ke `127.0.0.1` aur Docker container ke `127.0.0.1` alag hain. Agent uses `http://travel:8001/mcp`, `http://policy:8002/mcp`, `http://work:8003/mcp`. Har server ka **apna** healthcheck apne localhost ko use karta hai.

## 6. Logs + metrics

```powershell
docker compose logs -f --tail=100 monitor
docker compose logs --tail=100 travel
```

`monitor.py` JSON logs emit karta hai; SDK/Uvicorn ke logs uniform JSON **nahin** hain. Docker `json-file` driver file format JSON hai, app ke har log message ka JSON hona guaranteed nahin.

Prometheus `mcp_protocol_up{service="policy"}`, `mcp_probe_duration_seconds`, `mcp_probe_failures_total` collect karta hai. Ye *availability probes* hain, model latency/token/cost/trace monitoring nahi. No public Prometheus port; internally use e.g. `docker compose exec prometheus wget -qO- http://monitor:9100/metrics` (image mein wget available hone par).

Probe availability MCP handshake verify karti hai; Gemini external service ki end-to-end availability nahi. Alerts, dashboards aur tracing future enhancement hain.

## 7. Security boundaries & limitations

- Booking token validation + scope authorization + SQLite one-time approval remain enabled. Tokens learning demo ke static env values hain, **OAuth/JWT production auth nahin**. Isko public Internet par expose nahi karna.
- Travel/Policy/Work abhi unauthenticated hain, internal network access control ka substitute nahin. Enforce auth at ingress and ideally per service, mTLS, network segmentation, tool-level ACLs.
- `.env` ko `.gitignore`/`.dockerignore` mein exclude kiya hai, lekin `env_file` se credentials container ENV mein hotay hain (Docker operators unhein inspect kar sakte hain). Production secret manager + rotation + least privilege chahiye.
- Booking SQLite local named volume single-instance demo hai; multi-node high availability ke liye Postgres aur atomic workflow transitions chahiye.
- Work task list in-memory hai aur restart par reset hoti hai; production durable DB + approval for external side-effects.
- `docker compose up` deploy platform nahi; TLS reverse proxy, authenticated gateway, auditing, backups, image pinning/scans aur staging load tests abhi baqi hain.
- Observability exporter sirf `travel/policy/work` check karta hai; protected booking alag Docker healthcheck se monitor hoti hai. Prometheus external access not enabled.

## 8. Common issues

- **unhealthy policy**: indexer run hua? `docker compose --profile tools run --rm indexer`.
- **embedding failure**: GOOGLE_API_KEY, quota, DNS/egress.
- **Groq failure**: GROQ_API_KEY and quota.
- **wrong URLs**: agent ko service-name URLs chahiye, host localhost nahi.
- **Port busy**: no published host ports in this Compose; host-side Class 8 unaffected.
- **401**: booking token verification; ensure role and proper token.
- **read-only**: only `rag_index` / `booking_state` mounted writeable, other filesystem readonly.

## 9. Practice

1. Index build karo; source document update kar ke stale-index validation dekho.
2. Policy container stop kar ke monitor metrics ka `mcp_protocol_up` drop observe karo.
3. `docker compose restart work` aur in-memory tasks reset confirm karo.
4. Traveler scope se approve/execute ka attempt fail hota verify karo.
5. `/metrics` service ko host public port par expose kiye baghair scrape karo.

## 10. Further production checklist

HTTPS ingress + proper OAuth 2.1 resource verification, non-static identities, least privilege, auth for *all* MCP tools, audit logs, tracing, model cost/latency metrics, Prometheus Alertmanager, pinned immutable image digests, CI/CD tests, vulnerability scans, persistence backups and restore drill, high availability deployment, redaction/retention limits and incident runbook.
