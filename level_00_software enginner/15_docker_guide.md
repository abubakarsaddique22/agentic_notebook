# 🐳 Docker — Containers & Deployment (Section 0.7)
### Copy-paste guide · Windows CMD (Command Prompt) · Roman Urdu

**Kaise use karna hai:**
- Har command **CMD (Command Prompt)** mein chalao. Start menu mein `cmd` likho.
  VS Code ka terminal use karna ho to terminal ke `+` ke saath wale dropdown se **Command Prompt** chuno.
- Har code block mein **ek command** hai — copy karo, CMD mein paste karo, Enter dabao.
- Sections **upar se neeche** order mein karo — aage wale sections pichli images use karte hain.
- Jahan likha ho **"📄 File banao"** → VS Code mein wo file banao aur content paste kar ke save karo.
- Docker Desktop background mein chalta rahe (tray mein whale 🐳 icon).
- Ye `.md` file `docker_lab` folder ke **bahar** rakho.

---

## 0️⃣ Setup

Lab folder banao:
```bat
mkdir %USERPROFILE%\docker_lab
```

Us folder mein jao:
```bat
cd /d %USERPROFILE%\docker_lab
```

Folder VS Code mein kholo (files yahin banani hain):
```bat
code .
```

Docker chal raha hai? "Server" version aana chahiye:
```bat
docker version --format "Client: {{.Client.Version}} | Server: {{.Server.Version}} ({{.Server.Os}}/{{.Server.Arch}})"
```
> Error aaye ("cannot connect to the Docker daemon") → Docker Desktop open karo aur 1 minute ruko.

> Nayi CMD window kholo to pehle `cd /d %USERPROFILE%\docker_lab` zaroor chalao — saari commands isi folder se chalni hain.

---

## 1️⃣ App vs Environment vs Machine

| Cheez | Matlab | Example |
|---|---|---|
| **App** | Aap ka code | `app.py` |
| **Environment** | Code chalne ke liye sab kuch | Python version, libraries, env vars, OS |
| **Machine** | Hardware/server | Aap ka laptop, AWS server |

Docker App + Environment ko ek saath pack kar deta hai → machine koi bhi ho, andar sab same.

Aap ke PC ka Python version:
```bat
python --version
```

Container ka OS + Python (pehli baar `python:3.11-slim` image download hogi ~50 MB):
```bat
docker run --rm python:3.11-slim python -c "import platform; print(platform.system(), platform.release(), platform.python_version())"
```
👀 **Notice:** PC Windows hai, container ke andar **Linux** hai. Docker Desktop WSL2 ki halki Linux VM chalata hai.

- `--rm` = command khatam hote hi container delete

---

## 2️⃣ Image vs Container

- **Image** = template / recipe (read-only)
- **Container** = us image ka chalta hua roop. Ek image se kai containers.
- Container **ephemeral** hai — delete hua to andar ka data gaya.

Ek image se pehla container (5 minute zinda rahega):
```bat
docker run -d --name box1 python:3.11-slim sleep 300
```

Same image se doosra container:
```bat
docker run -d --name box2 python:3.11-slim sleep 300
```

Chalte containers dekho:
```bat
docker ps
```

box1 mein ek file likho:
```bat
docker exec box1 sh -c "echo hello-from-box1 > /tmp/note.txt && cat /tmp/note.txt"
```

box2 mein dekho — `note.txt` **NAHI** hogi (har container alag):
```bat
docker exec box2 ls /tmp
```

Ab box1 delete karo:
```bat
docker rm -f box1
```

box1 dobara banao:
```bat
docker run -d --name box1 python:3.11-slim sleep 300
```

File bachi? Dekho:
```bat
docker exec box1 ls /tmp
```
File gayab! Container delete = data gaya. Data rakhna ho to **VOLUME** use karo.

Safai:
```bat
docker rm -f box1 box2
```

| Flag / Command | Kya karta hai |
|---|---|
| `-d` | Background (detached) mein chalao |
| `--name box1` | Container ka naam |
| `docker exec` | Chalte container ke andar command |
| `docker rm -f` | Container zabardasti band + delete |

---

## 3️⃣ Dockerfile — apni API ki image banao

### 📄 File banao: `app.py`
```python
import os
from fastapi import FastAPI
from pydantic import BaseModel

# ---- Config env vars se (code mein hardcode nahi) ----
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY env var missing! App start nahi ho sakti.")

MODEL_NAME = os.getenv("MODEL_NAME", "tiny-sentiment-v1")
APP_ENV = os.getenv("APP_ENV", "development")
print(f"Starting model={MODEL_NAME} env={APP_ENV}")

app = FastAPI(title="Lab Sentiment API")

POSITIVE = {"good", "great", "love", "excellent", "awesome", "acha", "zabardast", "behtareen"}
NEGATIVE = {"bad", "worst", "hate", "terrible", "poor", "bura", "bekaar", "ghatiya"}

class Item(BaseModel):
    text: str

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "env": APP_ENV, "api_key_loaded": True}

@app.post("/predict")
def predict(item: Item):
    words = set(item.text.lower().split())
    score = len(words & POSITIVE) - len(words & NEGATIVE)
    label = "positive" if score > 0 else "negative" if score < 0 else "neutral"
    return {"text": item.text, "label": label, "score": score, "model": MODEL_NAME}
```

### 📄 File banao: `requirements.txt`
```
fastapi==0.115.0
uvicorn==0.30.6
```

### 📄 File banao: `Dockerfile` (koi extension nahi)
```dockerfile
# 1) Base image: chhota Debian + Python 3.11
FROM python:3.11-slim

# 2) Python ko container-friendly banao
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) Container ke andar kaam ka folder
WORKDIR /app

# 4) PEHLE sirf requirements copy + install (cache ke liye)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Phir baqi code copy
COPY . .

# 6) Documentation: app is port par sunti hai
EXPOSE 8000

# 7) Start command. PORT env var ho to wo, warna 8000
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### Dockerfile line-by-line

| Instruction | Kya karta hai | Kyun |
|---|---|---|
| `FROM python:3.11-slim` | Base image | `slim` chhoti hai; version pin = reproducible |
| `ENV PYTHONUNBUFFERED=1` | Output turant print | Warna `docker logs` mein logs der se aate hain |
| `WORKDIR /app` | `cd /app` | Agle commands yahin chalenge |
| `COPY requirements.txt .` | Sirf requirements pehle | Layer caching (section 5) |
| `RUN pip install` | **Build time** par chalta hai | Result image mein save |
| `COPY . .` | Baqi code | `.dockerignore` decide karta hai kya na jaye |
| `EXPOSE 8000` | Sirf documentation | Port khud **nahi** kholta, `-p` kholta hai |
| `CMD [...]` | **Run time** start command | `exec` → app ko stop signal sahi milta hai |

**`--host 0.0.0.0` kyun?** `127.0.0.1` = sirf container ke andar se suno → bahar se request nahi pahunchegi.

### Build karo

Image banao (`-t` = naam:tag, `.` = ye folder yaani build context):
```bat
docker build -t lab-api:v1 .
```

Bani hui image dekho:
```bat
docker images lab-api
```

---

## 4️⃣ Ports & Env Vars

```
docker run -p 9000:8000 ...
            │     └── CONTAINER port (app andar yahan sunti hai)
            └──────── HOST port (browser mein localhost:9000)
```
- `-e KEY=value` → ek env var
- `--env-file .env` → file se saare env vars
- Faida: **ek image**, dev/staging/prod mein sirf env vars alag

### API chalao

Container chalao — port 8000 kholo aur 2 env vars do:
```bat
docker run -d --name api1 -p 8000:8000 -e API_KEY=dev-key-123 -e MODEL_NAME=tiny-v1 lab-api:v1
```

### Test karo (`curl` Windows 10/11 mein built-in hai)

GET request — health check:
```bat
curl http://localhost:8000/health
```

POST request — positive text (JSON ke andar wale quotes `\"` se likhe hain):
```bat
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"text\":\"this watch is zabardast and great\"}"
```

POST request — negative text:
```bat
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"text\":\"service was bekaar\"}"
```

👉 Browser mein kholo: **http://localhost:8000/docs** (FastAPI ka Swagger UI — yahan se bhi test kar sakte ho, quotes ka jhanjhat nahi)

> Pehli request par error aaye to 2-3 second ruk kar dobara chalao — container start ho raha hota hai.

### Same image, doosra config, doosra port

Doosra container — host port 9000, alag env vars:
```bat
docker run -d --name api2 -p 9000:8000 -e API_KEY=other-key -e MODEL_NAME=tiny-v2 -e APP_ENV=staging lab-api:v1
```

Doosre container ka health check:
```bat
curl http://localhost:9000/health
```

api1 ki port mapping dekho:
```bat
docker port api1
```

api2 ki port mapping dekho:
```bat
docker port api2
```
Dono andar 8000 par hain, bahar alag ports (8000, 9000). Ek image, do configs.

### Container ke andar env vars dekho (debugging ke liye)
```bat
docker exec api1 printenv API_KEY MODEL_NAME APP_ENV
```
⚠️ Jis ke paas docker access hai wo ye dekh sakta hai.

### 🪤 Trap #1: App `127.0.0.1` par

Image ke baad diya command CMD ko override kar deta hai — app ko 127.0.0.1 par chalao:
```bat
docker run -d --name api-bad -p 8001:8000 -e API_KEY=x lab-api:v1 uvicorn app:app --host 127.0.0.1 --port 8000
```

Logs dekho (normal lagenge):
```bat
docker logs api-bad
```

Request bhejo:
```bat
curl http://localhost:8001/health
```
Logs normal, container "Up", magar curl **FAIL** ❌ → fix: `--host 0.0.0.0`

Safai:
```bat
docker rm -f api-bad
```

### 🪤 Trap #2: Host port pehle se busy

api1 pehle hi 8000 le chuka hai — dobara 8000 try karo:
```bat
docker run -d --name api-clash -p 8000:8000 -e API_KEY=x lab-api:v1
```
Error: `port is already allocated` → fix: doosra host port, jaise `-p 8002:8000`

Safai:
```bat
docker rm -f api-clash api1 api2
```

### ⚠️ Common mistakes
- `EXPOSE` likh kar sochna port khul gaya → `-p` chahiye.
- Container ke andar `localhost` = **container khud**, aap ka PC nahi. PC ki cheez (jaise local DB) ke liye `host.docker.internal`.

---

## 5️⃣ Image Layers & .dockerignore

**Layers:** Har `RUN`/`COPY` ek layer. Docker layers cache karta hai. **Ek layer badli → neeche ki saari dobara banti hain.**
Rule: kam badalne wali cheezen upar (requirements), zyada badalne wali neeche (code).

Har layer aur uska size dekho:
```bat
docker history lab-api:v1
```
pip install wali layer sab se bari hogi.

### Cache dekho

Kuch nahi badla → sab CACHED, build second mein:
```bat
docker build --progress=plain -t lab-api:v1 .
```
Output mein `CACHED` lines dekho.

Ab sirf code badlo (`app.py` ke aakhir mein ek comment add hoga):
```bat
echo # small code change>> app.py
```

Dobara build:
```bat
docker build --progress=plain -t lab-api:v1 .
```
pip install **CACHED** raha, sirf `COPY . .` dobara chala ✅

### GALAT order — 📄 File banao: `Dockerfile.slow`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Pehli build (`-f` = konsi Dockerfile use karni hai):
```bat
docker build --progress=plain -f Dockerfile.slow -t lab-api:slow .
```

Sirf ek comment badlo:
```bat
echo # another tiny change>> app.py
```

Dobara build:
```bat
docker build --progress=plain -f Dockerfile.slow -t lab-api:slow .
```
Ek comment badla aur pip install **DOBARA** chala ❌ (torch jaisi libraries mein minutes ka nuksaan)

### .dockerignore — pehle BINA iske leak dekho

📄 **File banao: `.env`**
```
API_KEY=prod-super-secret-999
MODEL_NAME=tiny-v2
APP_ENV=production
```

`data` folder banao:
```bat
mkdir data
```

Usmein 50 MB ka fake dataset banao:
```bat
python -c "open('data/big_dataset.bin','wb').write(b'\0'*50*1024*1024)"
```

Build karo (abhi `.dockerignore` nahi hai):
```bat
docker build -t lab-api:noignore .
```

Image ke andar kya gaya? Dekho:
```bat
docker run --rm lab-api:noignore ls -la /app
```

`.env` ka content image ke andar se parho:
```bat
docker run --rm lab-api:noignore cat /app/.env
```
🚨 **SECRET image ke andar hai!** Docker Hub par push hui to koi bhi parh lega.

### 📄 File banao: `.dockerignore`
```
# Secrets
.env
.env.*

# Data / models
data/
*.bin
*.pt
*.ckpt

# Python junk
__pycache__/
*.pyc
.venv/
venv/

# Tools / docs
.git/
.vscode/
*.ipynb
*.md
Dockerfile.*
```

Ab `.dockerignore` ke saath build:
```bat
docker build -t lab-api:v2 .
```

Andar dekho — `.env` aur `data/` hone chahiye **nahi**:
```bat
docker run --rm lab-api:v2 ls -la /app
```

Sizes compare karo:
```bat
docker images lab-api
```
✅ `.env` aur `data/` gayab, aur noignore wali image ~50 MB bari hai.

### ⚠️ Common mistakes
- `COPY . .` ko `pip install` se pehle rakhna.
- `.dockerignore` bhoolna → `.env`, `.git`, datasets image mein.
- `apt-get update` aur `apt-get install` alag `RUN` mein → ek hi `RUN` mein `&&` se jodo.

---

## 6️⃣ Logs & Startup Failures

**Startup failure ki 2 sab se common wajah: missing env var ya galat port.**

### 🔍 Debugging checklist (isi order mein)
1. `docker ps -a` → chal raha hai ya **Exited**? Exit code?
2. `docker logs <name>` → error message
3. `docker inspect <name>` → env vars, ports, exit code
4. `docker exec <name> printenv` → config andar pahuncha?
5. Ports → app kis port aur `0.0.0.0` par sun rahi hai? `-p` match karta hai?
6. Sahi image/tag chal rahi hai? `docker images`

### Exit codes

| Code | Matlab |
|---|---|
| `0` | Normal khatam (web server ke liye ye bhi masla) |
| `1` | App error (Python exception) |
| `125` | `docker run` khud fail (galat flag, port busy) |
| `126` | Command chal nahi saka (permission) |
| `127` | Command mila hi nahi (typo / install nahi) |
| `137` | SIGKILL — aksar **OOM (memory khatam)** |
| `143` | SIGTERM — graceful stop |

### Failure #1: Missing env var

Container chalao — `API_KEY` jaan-boojh kar **nahi** diya:
```bat
docker run -d --name crash1 -p 8000:8000 lab-api:v2
```

Chalte containers — crash1 nahi dikhega:
```bat
docker ps
```

Saare containers — yahan dikhega `Exited (1)`:
```bat
docker ps -a
```

Exit code nikalo:
```bat
docker inspect crash1 --format "ExitCode={{.State.ExitCode}}"
```

Asal wajah logs mein:
```bat
docker logs --tail 15 crash1
```
Logs mein: `RuntimeError: API_KEY env var missing!`

Safai:
```bat
docker rm -f crash1
```

### Failure #2: Galat port mapping

App andar 8000 par hai, magar mapping 5000 ki kar di:
```bat
docker run -d --name crash2 -p 8000:5000 -e API_KEY=x lab-api:v2
```

Request bhejo — fail hogi:
```bat
curl http://localhost:8000/health
```

Status dekho — phir bhi "Up" hai:
```bat
docker ps
```

Logs dekho — `running on 0.0.0.0:8000` likha hoga:
```bat
docker logs --tail 5 crash2
```
Logs ka port (8000) vs `-p` ka right side (5000) — match nahi karta!

Safai:
```bat
docker rm -f crash2
```

Fix: `PORT` env var se app ko hi 5000 par chalao (cloud platforms yahi karte hain):
```bat
docker run -d --name fixed -p 8000:5000 -e PORT=5000 -e API_KEY=x lab-api:v2
```

Ab request kaam karegi:
```bat
curl http://localhost:8000/health
```

Safai:
```bat
docker rm -f fixed
```

### Log commands

Saare logs:
```bat
docker logs api1
```

Aakhri 50 lines:
```bat
docker logs --tail 50 api1
```

Live follow (Ctrl+C se band):
```bat
docker logs -f api1
```

Pichle 10 minute ke logs:
```bat
docker logs --since 10m api1
```

Timestamps ke saath:
```bat
docker logs -t api1
```

### ⚠️ Common mistakes
- Logs nahi aa rahe → `PYTHONUNBUFFERED=1` nahi lagaya.
- App logs file mein likh rahi hai → container mein **stdout** par log karo.
- Crash loop mein sirf `docker ps` dekhna → `docker ps -a` + logs.
- Logs khaali hon to andar ja kar dekho (bahar aane ke liye `exit`):
```bat
docker run -it --entrypoint sh lab-api:v2
```

---

## 7️⃣ Deploying to a Public URL

```
 Aap ka PC  ── docker push ──►  Docker Hub  ── pull ──►  Cloud Platform  ──►  https://myapi...
```
- **Registry** = images ka GitHub (Docker Hub, GHCR, AWS ECR)
- **Platform** image chalata hai, HTTPS URL deta hai, crash par restart karta hai, aur aksar apna `PORT` env var deta hai

| Platform | Kab |
|---|---|
| Render / Railway / Fly.io | Demo, portfolio, chhote clients |
| Hugging Face Spaces (Docker) | AI demos (default port 7860) |
| Google Cloud Run / AWS App Runner | Serverless containers |
| AWS ECS / Kubernetes | Bari production systems |

### Step 1: Docker Hub par push
1. [hub.docker.com](https://hub.docker.com) par free account banao.

Docker Hub mein login:
```bat
docker login
```

Image ko Docker Hub wala naam do (`USERNAME` ki jagah apna username):
```bat
docker tag lab-api:v2 USERNAME/lab-api:v2
```

Push karo:
```bat
docker push USERNAME/lab-api:v2
```
- `docker tag` nayi image nahi banata — same image ko naya naam deta hai.
- Push ki hui image **public** hai — isi liye `.env` andar nahi honi chahiye.

### Step 2: Render par deploy
1. Render → **New → Web Service**
2. Source: **Existing image** → `docker.io/USERNAME/lab-api:v2`
   (Ya code GitHub par daalo, Render `Dockerfile` se khud build karega)
3. **Environment variables:** `API_KEY` = strong secret, `APP_ENV` = `production`, `MODEL_NAME` = `tiny-v2`
4. Deploy → **Logs** tab mein `Uvicorn running on 0.0.0.0:<port>` dekho

Public URL test karo (`YOUR-APP` ki jagah apna Render URL):
```bat
curl https://YOUR-APP.onrender.com/health
```

Public URL par predict:
```bat
curl -X POST https://YOUR-APP.onrender.com/predict -H "Content-Type: application/json" -d "{\"text\":\"deployment was zabardast\"}"
```
> Free tiers aur dashboard ke options badalte rehte hain — sign up par current pricing check karo.

### ⚠️ Common mistakes
- App fixed port par, platform `PORT` kuch aur de raha → "deploy timed out".
- Free tier par pehli request slow (**cold start**) — bug nahi.
- ARM (Mac M-series) par build, x86 server → `exec format error`. Fix: `--platform linux/amd64`.

---

## 8️⃣ Production Env Vars & Secrets

### 🔐 Golden rules
1. Secrets **kabhi** image mein nahi — na `ENV`, na `ARG`, na `COPY .env`
2. Secrets **kabhi** git mein nahi — `.env` ko `.gitignore` aur `.dockerignore` dono mein
3. Dev aur prod ki **alag keys**
4. Production mein secrets platform ke env vars / secret manager se
5. Code mein `os.getenv()`, hardcode nahi

### ❌ Galat tareeqa — 📄 File banao: `Dockerfile.bad`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
# ❌ NEVER DO THIS
ENV API_KEY=sk-live-THIS-IS-LEAKED-123
CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Galat Dockerfile se build:
```bat
docker build -f Dockerfile.bad -t lab-api:bad .
```

Koi bhi jiske paas image hai, secret nikal sakta hai — tareeqa 1:
```bat
docker inspect lab-api:bad --format "{{json .Config.Env}}"
```

Tareeqa 2 (layer history se):
```bat
docker history --no-trunc lab-api:bad | findstr API_KEY
```
🚨 Plain text! Baad mein hata do tab bhi purani layer mein rehta hai.

### ✅ Sahi tareeqa — runtime par env file

📄 **File banao: `.env.dev`**
```
API_KEY=dev-key-not-secret
MODEL_NAME=tiny-dev
APP_ENV=development
```

📄 **File banao: `.env.prod`**
```
API_KEY=prod-very-strong-secret
MODEL_NAME=tiny-v2
APP_ENV=production
```

Dev config ke saath container (port 8000):
```bat
docker run -d --name api-dev -p 8000:8000 --env-file .env.dev lab-api:v2
```

Prod config ke saath container (port 8001):
```bat
docker run -d --name api-prod-env -p 8001:8000 --env-file .env.prod lab-api:v2
```

Dev check:
```bat
curl http://localhost:8000/health
```

Prod check:
```bat
curl http://localhost:8001/health
```
✅ **SAME image**, alag config, image mein koi secret nahi.

Safai:
```bat
docker rm -f api-dev api-prod-env
```

### Bonus: Production-grade — 📄 File banao: `Dockerfile.prod`
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Non-root user banao
RUN useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser app.py .
USER appuser

EXPOSE 8000

# slim image mein curl nahi hota, is liye Python se health check
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["sh", "-c", "exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Prod image build:
```bat
docker build -f Dockerfile.prod -t lab-api:prod .
```

Prod env file ke saath chalao:
```bat
docker run -d --name api-prod -p 8000:8000 --env-file .env.prod lab-api:prod
```

Container kis user se chal raha hai? `root` nahi, `appuser` aana chahiye:
```bat
docker exec api-prod whoami
```

Health check:
```bat
curl http://localhost:8000/health
```

Docker ka health status — pehle `starting`, ~10 sec baad `healthy` (2-3 dafa chalao):
```bat
docker inspect api-prod --format "{{.State.Health.Status}}"
```

STATUS column mein `(healthy)` dikhega:
```bat
docker ps
```

Safai:
```bat
docker rm -f api-prod
```

### ⚠️ Common mistakes
- `.env` git mein push ho gaya → delete kaafi nahi (history mein hai). **Key turant rotate karo.**
- `--build-arg` se secret → `docker history` mein dikhta hai.
- Production mein `DEBUG=True` ya dev keys.

---

## 9️⃣ 🎤 Top Interview Sawal (short jawab)

| Sawal | Jawab |
|---|---|
| Image vs container? | Read-only template vs running instance (class vs object) |
| Container vs VM? | Container host ka kernel share karta hai (MBs, seconds); VM ka apna OS (GBs, minutes, zyada strong isolation) |
| RUN vs CMD vs ENTRYPOINT? | RUN = build time; CMD = default start command (override ho sakta); ENTRYPOINT = fixed executable, args aage lagte hain |
| COPY vs ADD? | COPY sirf local files; ADD tar extract + URL bhi. COPY prefer karo |
| slim vs alpine? | Alpine musl use karta hai → numpy/torch wheels masla. Python/ML ke liye slim |
| `latest` kyun avoid? | Waqt ke saath badalta hai → reproducible nahi. Version ya git SHA pin karo |
| EXPOSE port kholta hai? | Nahi, sirf documentation. `-p` kholta hai |
| Layer caching? | Instruction + files same → cached. Ek layer badli to neeche sab dobara |
| Image size kam? | slim, .dockerignore, `--no-cache-dir`, multi-stage build, CPU-only torch |
| Exit code 137? | SIGKILL, aksar OOM (memory limit). ML model load mein common |
| Secrets kaise doge? | Runtime par: `-e`, `--env-file`, platform env vars, secret manager. Image/git mein kabhi nahi |
| `RUN rm .env` safe? | Nahi, purani layer mein file rehti hai. `.dockerignore` + key rotate |
| Non-root kyun? | Hack ho to attacker root na ho (least privilege) |
| Container ke andar `localhost`? | Container khud, host nahi |
| Namespaces vs cgroups? | Isolation (kya dikhta) vs resource limits (kitna use) |

### 🧩 "Local par chalta hai, prod mein nahi" — kya check karoge?
1. **Logs** — platform logs mein exact error
2. **Env vars** — prod mein koi missing? (sab se common)
3. **Port/host** — platform ka `PORT` use ho raha hai aur `0.0.0.0`?
4. **Image mismatch** — wahi tag/version chal raha hai?
5. **Architecture** — ARM build, x86 server → `exec format error`
6. **File paths & case** — Windows case-insensitive, Linux nahi (`Model.pkl` ≠ `model.pkl`)
7. **Network** — DB URL `localhost` (container mein galat), firewall
8. **Memory** — prod limit kam → 137 OOM
9. **Local par reproduce** — prod wali image + prod jaisi env vars se `docker run`

### 🤖 AI-specific
- **GPU:** NVIDIA Container Toolkit + CUDA base image + `docker run --gpus all`
- **Model weights (5 GB):** chhote model image mein bake; bare model external storage (HF Hub/S3) + cache volume + pinned version
- **LLM API serve:** model startup par ek dafa load, health/readiness endpoint, lamba `--start-period`, workers × model memory ka hisaab

---

## 🔟 Cheat Sheet (CMD)

| Kaam | Command |
|---|---|
| Lab folder mein jana | `cd /d %USERPROFILE%\docker_lab` |
| Image banana | `docker build -t name:tag .` |
| Alag Dockerfile se | `docker build -f Dockerfile.prod -t name:prod .` |
| Images dekhna | `docker images` |
| Container chalana | `docker run -d --name api -p 8000:8000 -e KEY=val name:tag` |
| Env file se | `docker run --env-file .env.prod name:tag` |
| Chalte containers | `docker ps` |
| Saare containers | `docker ps -a` |
| Logs | `docker logs --tail 50 api` / `docker logs -f api` |
| Andar command | `docker exec api printenv` |
| Andar shell | `docker exec -it api sh` (bahar aane ke liye `exit`) |
| Details | `docker inspect api` |
| Live CPU/RAM | `docker stats` (Ctrl+C se band) |
| Port mapping | `docker port api` |
| Layers | `docker history name:tag` |
| Output filter | `docker history --no-trunc name:tag \| findstr API_KEY` |
| Stop / remove | `docker stop api` / `docker rm -f api` |
| Image delete | `docker rmi name:tag` |
| Tag + push | `docker tag name:tag user/name:tag` → `docker push user/name:tag` |
| Disk usage | `docker system df` |
| Safai | `docker system prune` |
| API test (GET) | `curl http://localhost:8000/health` |
| API test (POST) | `curl -X POST URL -H "Content-Type: application/json" -d "{\"text\":\"hello\"}"` |

---

## 🏋️ Practice Exercises
1. **Port badlo:** API ko host port `7000` par chalao aur `/docs` browser mein kholo.
2. **Naya env var:** `app.py` mein `MAX_TEXT_LEN` (default 200) add karo; text lamba ho to error. Rebuild kar ke `-e MAX_TEXT_LEN=10` se test.
3. **Crash detective:** `requirements.txt` se `uvicorn` hata kar build/run karo. Exit code aur logs kya kehte hain? (Hint: 127.) Wapis add karna.
4. **Multi-stage:** `Dockerfile.prod` ko multi-stage banao — builder mein `pip wheel`, final mein sirf wheels install. Size compare karo.
5. **Compose:** `compose.yaml` likho jo API + `redis:7` chalaye, `docker compose up -d` se test.
6. **Deploy:** Section 7 se apna public URL banao — Fiverr/portfolio par dikhane wali cheez.

> **Outcome check ✅:** Bina notes dekhe "local par chalta hai, prod mein nahi" ka checklist bata sakte ho? Haan → section 0.7 complete.

---

## 🧹 Cleanup

Lab ke saare containers hatao ("No such container" errors normal hain):
```bat
docker rm -f box1 box2 api1 api2 api-bad api-clash crash1 crash2 fixed api-dev api-prod-env api-prod
```

Lab ki images hatao:
```bat
docker rmi lab-api:v1 lab-api:v2 lab-api:slow lab-api:noignore lab-api:bad lab-api:prod
```

Disk usage dekho:
```bat
docker system df
```
> `python:3.11-slim` rehne do — agli dafa download nahi karni padegi. Poori safai: `docker image prune -a`
