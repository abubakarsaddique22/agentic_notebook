# 09 — Self-Hosting (Langfuse ka khaas feature)

Langfuse **open-source (MIT)** hai. Matlab: apne laptop / company server par free mein chala sakte ho.
Data tumhare server se bahar nahi jata — banks, hospitals, aur privacy-conscious clients isi wajah se Langfuse chunte hain.
Freelancing mein bhi yeh selling point hai: "aap ka data aap ke server par rahega".

> Seekhne ke liye **Langfuse Cloud** kaafi hai. Yeh folder optional hai — jab Docker aata ho tab karo.

---

## Local setup (Windows + Docker Desktop)

### 1. Docker Desktop install
https://www.docker.com/products/docker-desktop/ → install → restart → Docker Desktop open karo (whale icon green ho).
Check (PowerShell):
```powershell
docker --version
docker compose version
```

### 2. Langfuse download + start
```powershell
cd C:\Users\abubakar\Desktop
git clone https://github.com/langfuse/langfuse.git langfuse-server
cd langfuse-server
docker compose up
```
Pehli dafa images download hongi (kuch minute). Jab logs mein `Ready` aaye → browser mein:
**http://localhost:3000**

> `git` nahi hai to: https://git-scm.com/download/win se install karo.

### 3. Account + project + keys
1. localhost:3000 par **Sign up** (yeh account sirf tumhare local server par hai)
2. Organization → Project banao → Settings → **API Keys** → create

### 4. Apne learning code ko local server par point karo
`C:\Users\abubakar\Desktop\langfuse\.env` mein:
```
LANGFUSE_PUBLIC_KEY=pk-lf-...   (local server wali)
LANGFUSE_SECRET_KEY=sk-lf-...   (local server wali)
LANGFUSE_BASE_URL=http://localhost:3000
```
Phir koi bhi script chalao — traces ab tumhare **apne** Langfuse mein jayenge:
```powershell
python 01_setup_and_first_trace\01_check_connection.py
```

### 5. Band / dobara start
```powershell
# langfuse-server folder mein
docker compose down      # band (data volumes mein bacha rehta hai)
docker compose up -d     # background mein start
```

---

## Architecture (interview mein poocha jata hai)

```
Your app (SDK) ──OTel spans──> langfuse-web (UI + API, port 3000)
                                    │
                                    v
                               Redis (queue)
                                    │
                                    v
                            langfuse-worker (processing)
                              │              │
                              v              v
                         Postgres        ClickHouse         MinIO / S3
                       (users, prompts,  (traces, observations,  (raw events,
                        datasets, config) scores — fast analytics) media)
```

- **Postgres**: transactional data (projects, prompts, datasets)
- **ClickHouse**: tracing data (billions of rows, tez analytics)
- **Redis**: queue + cache
- **S3/MinIO**: raw event storage + media (images/audio)
- Production mein: Kubernetes (Helm chart) ya cloud (AWS/GCP/Azure) — docs mein guides hain

## Docker compose wala setup production ke liye nahi
Local/testing ke liye theek hai. Production mein: managed Postgres, ClickHouse cluster, S3, backups,
secrets change karna (`docker-compose.yml` mein default passwords hote hain), HTTPS.

## Cloud vs Self-host — kab kya?
| | Langfuse Cloud | Self-host |
|---|---|---|
| Setup | 2 minute | Docker / K8s chahiye |
| Maintenance | Langfuse karta hai | Tum (upgrades, backups) |
| Data location | Langfuse ke servers (EU/US) | Tumhare servers |
| Cost | Free tier, phir usage-based | Infra ka kharcha |
| Kab | Startups, freelance projects, seekhna | Strict privacy / compliance clients |
