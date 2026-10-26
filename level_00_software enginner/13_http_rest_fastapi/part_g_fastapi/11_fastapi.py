"""
FASTAPI: saare concepts ek file mein (apne customers / loan / students data par)
================================================================================

Is file mein har concept ki apni HEADING hai, phir theory (comments), phir code,
aur aakhir mein us concept ka demo function.

Har concept ki apni app hai (app_get, app_post, ...), is liye koi app doosri ko
overwrite nahi karti. (Pehle har jagah `app = FastAPI()` tha, to sirf aakhri bachti thi.)

CHALANE KE TAREEQE (Windows cmd, is file wale folder mein):

    python 11_fastapi.py            <- saare concepts ke demos order mein
    python 11_fastapi.py 5          <- sirf concept 5 ka demo
    python 11_fastapi.py 5 6 7      <- kuch concepts

    uvicorn 11_fastapi:app_post --reload      <- kisi bhi concept ki app asli server ki tarah
    uvicorn 11_fastapi:app --reload           <- aakhri app (sab kuch ek saath, concept 16)
    phir browser: http://127.0.0.1:8000/docs

    python -m pytest 11_fastapi.py -v         <- concept 15 ke tests

Install (ek baar):  pip install "fastapi[standard]" httpx pydantic-settings pytest

CONCEPTS:
     1. GET method                          (zip: g02)
     2. POST method + Pydantic BaseModel    (zip: g04)
     3. Path parameter                      (zip: g03)
     4. Query parameter                     (zip: g03)
     5. Validation: Path, Query, Field, Literal   (zip: g03, g04)
     6. Response model + status codes (201, 409)  (zip: g04)
     7. Exception handling + ek jaisa error format (zip: g05)
     8. Dependency Injection (Depends)      (zip: g06)
     9. APIRouter                           (zip: g07)
    10. Sync vs Async                       (zip: g08)
    11. Settings (.env) + Lifespan + doosri API ko call  (zip: g09)
    12. Middleware + CORS                   (zip: g10)
    13. Webhook + Background tasks          (zip: g11)
    14. Streaming response                  (zip: g12)
    15. Testing (TestClient + pytest)       (zip: g13, Part H)
    16. Sab kuch ek app mein                (zip: Part H)
"""
import asyncio
import hashlib
import hmac
import json
import logging
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Literal

import httpx
from fastapi import (APIRouter, BackgroundTasks, Depends, FastAPI, Header, HTTPException,
                     Path, Query, Request, status)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("loan_api")


# =============================================================================
# DATA (poori file yahi data use karti hai)
# =============================================================================
CUSTOMERS = {
    "101": {"name": "Alice", "city": "New York", "risk_score": 75},
    "102": {"name": "Bob", "city": "Los Angeles", "risk_score": 45},
    "103": {"name": "Charlie", "city": "Chicago", "risk_score": 90},
    "104": {"name": "David", "city": "Houston", "risk_score": 60},
}

STUDENTS = {
    "s001": {"name": "Alice", "marks": 20, "major": "Computer Science"},
    "s002": {"name": "Bob", "marks": 15, "major": "Mathematics"},
    "s003": {"name": "Charlie", "marks": 18, "major": "Physics"},
    "s004": {"name": "David", "marks": 22, "major": "Chemistry"},
}


def heading(text: str) -> None:
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


# =============================================================================
# 1. GET METHOD
# =============================================================================
# GET = server se data PARHNA. Server par kuch badalta nahi (safe).
# - @app.get("/raasta") decorator batata hai: is URL par GET aaye to ye function chalao
# - Function jo dict return kare, FastAPI usay khud JSON bana deta hai
# - customer_id: int ki koi default value NAHI hai, is liye ye REQUIRED query param hai:
#     /customer?customer_id=101   ✅
#     /customer                   ❌ 422 (field required)
#     /customer?customer_id=abc   ❌ 422 (int nahi)

app_get = FastAPI(title="1. GET method")


@app_get.get("/customer")
def customer(customer_id: int):
    return {
        "customer_id": customer_id,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "status": "active",
        "created_at": "2023-01-01T12:00:00Z",
    }


def demo_1_get():
    tc = TestClient(app_get)
    for url in ["/customer?customer_id=101", "/customer", "/customer?customer_id=abc"]:
        r = tc.get(url)
        print(f"{r.status_code}  {url:<28} -> {str(r.json())[:80]}")


# =============================================================================
# 2. POST METHOD + PYDANTIC BaseModel
# =============================================================================
# POST = server ko naya data BHEJNA (body mein, JSON).
# - BaseModel batata hai body ki SHAKAL kya hogi (kaunse fields, kaunsi type)
# - FastAPI JSON ko parse + validate kar ke `data` object bana deta hai
# - Ghalat type (age: "abc") ya missing field -> khud 422
# - async def: yahan andar koi await nahi, to `def` bhi theek hai (concept 10 dekhein)
#
# Loan rule: income 50,000 se zyada AUR kam az kam 2 saal ki job -> Approved
# (Pehle `and data.employment_year` tha: 1 saal ho ya 30, sab pass ho jata tha)

app_post = FastAPI(title="2. POST method")


class LoanApplication(BaseModel):
    age: int
    income: float
    loan_amount: float
    employment_year: int


@app_post.post("/predict")
async def predict(data: LoanApplication):
    if data.income > 50000 and data.employment_year >= 2:
        decision = "Approved"
    else:
        decision = "Rejected"
    return {"age": data.age, "decision": decision}


def demo_2_post():
    tc = TestClient(app_post)
    apps = [
        {"age": 30, "income": 80000, "loan_amount": 200000, "employment_year": 5},
        {"age": 22, "income": 80000, "loan_amount": 200000, "employment_year": 1},
        {"age": 40, "income": 30000, "loan_amount": 100000, "employment_year": 10},
        {"age": "abc", "income": 80000, "loan_amount": 1},                     # ghalat
    ]
    for body in apps:
        r = tc.post("/predict", json=body)
        print(r.status_code, r.json() if r.is_success else [e["loc"][-1] + ": " + e["msg"] for e in r.json()["detail"]])


# =============================================================================
# 3. PATH PARAMETER
# =============================================================================
# Path param = URL ke RAASTE ka hissa, kisi EK cheez ki pehchaan: /risk-profile/101
# - URL mein {customer_id} aur function argument ka naam SAME hona chahiye
# - Na mile to `return {"error": ...}` NAHI (ye 200 OK ke saath jata hai, client
#   samjhe ga sab theek hai). Sahi: raise HTTPException(404, ...)
# - Ek URL mein kai path params ho sakte hain (doosra example)

app_path = FastAPI(title="3. Path parameter")


@app_path.get("/risk-profile/{customer_id}")
def get_risk_profile(customer_id: str):
    if customer_id not in CUSTOMERS:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CUSTOMERS[customer_id]


# Do path params. REST style: /customers/{id}/... (resource ke neeche resource)
@app_path.get("/customers/{customer_id}/name/{customer_name}")
def check_customer_name(customer_id: str, customer_name: str):
    customer = CUSTOMERS.get(customer_id)
    if customer is None or customer["name"] != customer_name:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": customer_id, **customer}


def demo_3_path():
    tc = TestClient(app_path)
    for url in ["/risk-profile/101", "/risk-profile/999",
                "/customers/102/name/Bob", "/customers/102/name/Alice"]:
        r = tc.get(url)
        print(f"{r.status_code}  {url:<28} -> {r.json()}")


# =============================================================================
# 4. QUERY PARAMETER
# =============================================================================
# Query param = URL mein ? ke baad: /customers?city=Chicago&min_risk_score=50
# - Additional info: filter, sort, search, pagination
# - Default value di (= None) -> OPTIONAL. Na di -> REQUIRED (concept 1)
# - Type hint: `str | None = None` likhein (sirf `str = None` type ke hisaab se ghalat hai)
# - Path param vs Query param: path = KAUNSI cheez, query = KAISI cheezein (filter)

app_query = FastAPI(title="4. Query parameter")


@app_query.get("/customers")
def filter_customers(city: str | None = None, min_risk_score: int | None = None):
    result = [{"id": cid, **c} for cid, c in CUSTOMERS.items()]
    if city:
        result = [c for c in result if c["city"] == city]
    if min_risk_score is not None:
        result = [c for c in result if c["risk_score"] >= min_risk_score]
    return result


def demo_4_query():
    tc = TestClient(app_query)
    for params in [{}, {"city": "Chicago"}, {"min_risk_score": 60}, {"city": "Houston", "min_risk_score": 70}]:
        r = tc.get("/customers", params=params)
        print(f"{str(params):<40} -> {[c['name'] for c in r.json()]}")


# =============================================================================
# 5. VALIDATION: Path(), Query(), Field(), Literal
# =============================================================================
# Sirf type (int/str) kaafi nahi. Asli rules bhi chahiye:
#   Annotated[str, Path(pattern=r"^\d{3}$")]       -> customer id sirf 3 digit
#   Annotated[int, Query(ge=0, le=100)]            -> 0 se 100 ke beech
#   Annotated[str, Query(min_length=2)]            -> kam az kam 2 huroof
#   Literal["New York", "Chicago", ...]            -> sirf yahi values allowed
#   Field(gt=0, le=100) BaseModel ke andar         -> body ke fields ki validation
# Rule toota -> FastAPI khud 422 + batata hai kaunsa field aur kyun.
# ge = greater or equal (>=), gt = greater than (>), le = <=, lt = <

app_validation = FastAPI(title="5. Validation")

City = Literal["New York", "Los Angeles", "Chicago", "Houston"]


@app_validation.get("/customers/{customer_id}")
def get_customer(customer_id: Annotated[str, Path(pattern=r"^\d{3}$")]):
    if customer_id not in CUSTOMERS:
        raise HTTPException(404, "Customer not found")
    return CUSTOMERS[customer_id]


@app_validation.get("/customers")
def search_customers(
    city: City | None = None,
    min_risk_score: Annotated[int, Query(ge=0, le=100)] = 0,
    name: Annotated[str | None, Query(min_length=2, max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
):
    result = [{"id": cid, **c} for cid, c in CUSTOMERS.items()
              if (city is None or c["city"] == city)
              and c["risk_score"] >= min_risk_score
              and (name is None or name.lower() in c["name"].lower())]
    return result[:limit]


class ValidLoanApplication(BaseModel):
    age: int = Field(ge=18, le=70)
    income: float = Field(gt=0)
    loan_amount: float = Field(gt=0, le=10_000_000)
    employment_year: int = Field(ge=0, le=50)


@app_validation.post("/predict")
def validated_predict(data: ValidLoanApplication):
    approved = data.income > 50000 and data.employment_year >= 2
    return {"age": data.age, "decision": "Approved" if approved else "Rejected"}


def demo_5_validation():
    tc = TestClient(app_validation)
    for url in ["/customers/101", "/customers/1", "/customers?city=Chicago",
                "/customers?city=Lahore", "/customers?min_risk_score=150", "/customers?name=a"]:
        r = tc.get(url)
        out = r.json() if r.is_success else r.json()["detail"][0]["msg"]
        print(f"{r.status_code}  {url:<32} -> {str(out)[:70]}")
    r = tc.post("/predict", json={"age": 15, "income": -5, "loan_amount": 0, "employment_year": 2})
    print(r.status_code, "POST /predict (ghalat values):")
    for e in r.json()["detail"]:
        print("     ", e["loc"][-1], "->", e["msg"])


# =============================================================================
# 6. RESPONSE MODEL + STATUS CODES (201, 409)
# =============================================================================
# - StudentIn  = jo client BHEJTA hai (password ke saath)
# - StudentOut = jo client ko MILTA hai (password aur internal_note NAHI)
# - response_model=StudentOut -> FastAPI jawab ko filter kar deta hai, chahe aap
#   poora dict lautayein. Secret fields kabhi galti se bahar nahi jayen ge.
# - status_code=201 -> "naya bana" (create par 200 ki jagah)
# - 409 Conflict -> current data se takraav (jaise same id dobara register)

app_response = FastAPI(title="6. Response model")


class StudentIn(BaseModel):
    student_id: Annotated[str, Field(pattern=r"^s\d{3}$")]
    name: Annotated[str, Field(min_length=2, max_length=50)]
    marks: Annotated[int, Field(ge=0, le=25)]
    major: str
    password: Annotated[str, Field(min_length=8)]


class StudentOut(BaseModel):
    student_id: str
    name: str
    marks: int
    major: str


registered: dict[str, dict] = {}


@app_response.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def register_student(student: StudentIn):
    if student.student_id in registered or student.student_id in STUDENTS:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ye student id pehle se registered hai")
    registered[student.student_id] = {**student.model_dump(), "internal_note": "scholarship"}
    return registered[student.student_id]          # poora dict, response_model filter kare ga


@app_response.get("/students/{student_id}", response_model=StudentOut)
def read_student(student_id: str):
    if student_id in STUDENTS:
        return {"student_id": student_id, **STUDENTS[student_id]}
    if student_id in registered:
        return registered[student_id]
    raise HTTPException(404, "Student not found")


def demo_6_response_model():
    registered.clear()
    tc = TestClient(app_response)
    new = {"student_id": "s005", "name": "Ali", "marks": 21, "major": "AI", "password": "secret123"}
    r = tc.post("/students", json=new)
    print(r.status_code, r.json(), "<- password/internal_note gayab")
    r = tc.post("/students", json=new)
    print(r.status_code, r.json(), "<- duplicate")
    print(tc.get("/students/s001").json())


# =============================================================================
# 7. EXCEPTION HANDLING + EK JAISA ERROR FORMAT
# =============================================================================
# Pehle wala student example ghalat tha: `if student_id in students` ki wajah se
# KeyError kabhi aata hi nahi tha, aur na milne par 200 + null jata tha.
# Sahi tareeqa: check karo, na mile to seedha raise HTTPException(404). try/except ki zaroorat nahi.
#
# Professional API mein HAR error ek hi shakal mein jata hai:
#     {"error": {"code": 404, "message": "...", "request_id": "..."}}
# Iske liye 3 handlers:
#   1. StarletteHTTPException -> 404/401/403 (+ "route hi nahi mila" wala 404)
#   2. RequestValidationError -> 422, field-wise saaf list
#   3. Exception              -> koi bhi crash: client ko sirf "Internal server error",
#                                poora traceback sirf LOGS mein (security)

app_errors = FastAPI(title="7. Exception handling")


def error_body(code: int, message: str, request: Request, details=None) -> dict:
    rid = getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or uuid.uuid4().hex[:8]
    body = {"error": {"code": code, "message": message, "request_id": rid}}
    if details:
        body["error"]["details"] = details
    return body


def add_error_handlers(app: FastAPI) -> None:
    """Kisi bhi app par teeno handlers laga do (concept 16 mein dobara use hoga)."""

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, headers=exc.headers,
                            content=error_body(exc.status_code, str(exc.detail), request))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=422, content=error_body(422, "Validation failed", request, details))

    @app.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content=error_body(500, "Internal server error", request))


add_error_handlers(app_errors)


@app_errors.get("/students/{student_id}")
def get_student(student_id: str):
    if student_id not in STUDENTS:
        raise HTTPException(status_code=404, detail="Student not found")
    return STUDENTS[student_id]


@app_errors.get("/students/{student_id}/percentage")
def student_percentage(student_id: str, total_marks: int = 25):
    if student_id not in STUDENTS:
        raise HTTPException(404, "Student not found")
    return {"percentage": STUDENTS[student_id]["marks"] / total_marks * 100}   # total_marks=0 -> crash!


def demo_7_errors():
    tc = TestClient(app_errors, raise_server_exceptions=False)
    for url in ["/students/s001", "/students/s999", "/ghalat-url",
                "/students/s001/percentage?total_marks=abc", "/students/s001/percentage?total_marks=0"]:
        r = tc.get(url, headers={"X-Request-ID": "req-7"})
        print(f"{r.status_code}  {url:<42} -> {json.dumps(r.json())[:95]}")
    print("Dekhein: ZeroDivisionError client ko nazar nahi aaya, sirf upar wale log mein hai.")


# =============================================================================
# 8. DEPENDENCY INJECTION (Depends)
# =============================================================================
# Dependency = function jo endpoint se PEHLE chalta hai, aur:
#   - kuch DETA hai (current user, pagination, settings, DB), ya
#   - request ROK deta hai (auth fail -> 401/403)
# Fayde: auth/pagination ka code ek jagah, dependencies ki chain, aur tests mein
# app.dependency_overrides se fake se badal sakte hain.
#
# 401 = "tum kaun ho?" (key nahi/ghalat) | 403 = "pehchaan liya, ijazat nahi"

app_deps = FastAPI(title="8. Dependencies")

API_KEYS = {"officer-key": {"name": "Loan Officer", "role": "officer"},
            "manager-key": {"name": "Branch Manager", "role": "manager"}}


def pagination(limit: Annotated[int, Query(ge=1, le=50)] = 2,
               offset: Annotated[int, Query(ge=0)] = 0) -> dict:
    return {"limit": limit, "offset": offset}


def current_user(x_api_key: Annotated[str | None, Header()] = None) -> dict:
    if x_api_key not in API_KEYS:
        raise HTTPException(401, "API key missing ya ghalat", headers={"WWW-Authenticate": "ApiKey"})
    return API_KEYS[x_api_key]


def require_manager(user: Annotated[dict, Depends(current_user)]) -> dict:      # chain
    if user["role"] != "manager":
        raise HTTPException(403, "Sirf manager ye kar sakta hai")
    return user


CurrentUser = Annotated[dict, Depends(current_user)]          # baar baar likhne se bachao
Page = Annotated[dict, Depends(pagination)]


@app_deps.get("/customers")
def list_customers(user: CurrentUser, page: Page):
    items = [{"id": cid, **c} for cid, c in CUSTOMERS.items()]
    return {"viewer": user["name"], "page": page,
            "items": items[page["offset"]:page["offset"] + page["limit"]], "total": len(items)}


@app_deps.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: str, manager: Annotated[dict, Depends(require_manager)]):
    logger.info("Customer %s delete hua (by %s) [demo: asal mein data nahi mitaya]", customer_id, manager["name"])


def demo_8_dependencies():
    tc = TestClient(app_deps)
    print(tc.get("/customers").status_code, "<- bina key")
    r = tc.get("/customers?limit=2&offset=2", headers={"X-API-Key": "officer-key"})
    print(r.status_code, r.json())
    print(tc.delete("/customers/101", headers={"X-API-Key": "officer-key"}).status_code, "<- officer delete (403)")
    print(tc.delete("/customers/101", headers={"X-API-Key": "manager-key"}).status_code, "<- manager delete (204)")

    app_deps.dependency_overrides[current_user] = lambda: {"name": "TestUser", "role": "officer"}
    print("Override (bina key):", tc.get("/customers").json()["viewer"])
    app_deps.dependency_overrides.clear()


# =============================================================================
# 9. APIRouter: app ko hisson mein baantna
# =============================================================================
# Bari app mein har feature (customers, loans, students) ka apna router hota hai,
# asal project mein alag file mein. Phir main app mein include_router se jorte hain.
# - prefix="/customers"            -> router ke saare raaste is se shuru
# - dependencies=[Depends(...)]    -> router ke SAARE endpoints protected
# - include_router(..., prefix="/v1") -> versioning: /v1/customers/101

customers_router = APIRouter(prefix="/customers", tags=["customers"],
                             dependencies=[Depends(current_user)])


@customers_router.get("/{customer_id}")
def router_get_customer(customer_id: Annotated[str, Path(pattern=r"^\d{3}$")]):
    if customer_id not in CUSTOMERS:
        raise HTTPException(404, "Customer not found")
    return {"id": customer_id, **CUSTOMERS[customer_id]}


loans_router = APIRouter(prefix="/loans", tags=["loans"])


@loans_router.post("/predict")
def router_predict(data: ValidLoanApplication):
    return validated_predict(data)


students_router = APIRouter(prefix="/students", tags=["students"])


@students_router.get("/{student_id}")
def router_get_student(student_id: str):
    return get_student(student_id)


app_routers = FastAPI(title="9. Routers")
for _r in (customers_router, loans_router, students_router):
    app_routers.include_router(_r, prefix="/v1")


def demo_9_routers():
    tc = TestClient(app_routers)
    print(tc.get("/v1/customers/103", headers={"X-API-Key": "officer-key"}).json())
    print(tc.get("/v1/customers/103").status_code, "<- router level auth (401)")
    print(tc.get("/v1/students/s002").json(), "<- students router par auth nahi")
    print("Saare raaste:", list(app_routers.openapi()["paths"]))


# =============================================================================
# 10. SYNC vs ASYNC (interview favorite)
# =============================================================================
# def        -> FastAPI isay THREAD POOL mein chalata hai. Blocking kaam (time.sleep,
#               requests.get, sync DB/LLM client) yahan theek hai.
# async def  -> EVENT LOOP par chalta hai (ek hi). Sirf tab jab andar `await` ho
#               (httpx.AsyncClient, asyncio.sleep, async LLM SDK).
#
# SAB SE BARI GHALTI: async def ke andar blocking code -> event loop phans jata hai,
# POORA server ruk jata hai. Demo: 5 requests ek saath, har ek 1 second ka kaam:
#   /credit-check/sync   ~1s  (har request alag thread)
#   /credit-check/bad    ~5s  (event loop par time.sleep, sab line mein)
#   /credit-check/good   ~1s  (await ke dauraan doosri requests chalti hain)
# CPU heavy kaam (model inference) -> def, ya alag worker. Async CPU tez nahi karta.

app_async = FastAPI(title="10. Sync vs Async")


@app_async.get("/credit-check/sync")
def credit_check_sync():
    time.sleep(1)                     # blocking, lekin def -> theek
    return {"ok": True}


@app_async.get("/credit-check/bad")
async def credit_check_bad():
    time.sleep(1)                     # ❌ blocking INSIDE async
    return {"ok": True}


@app_async.get("/credit-check/good")
async def credit_check_good():
    await asyncio.sleep(1)            # ✅ non-blocking
    return {"ok": True}


def demo_10_sync_async():
    import uvicorn

    os.environ["NO_PROXY"] = "127.0.0.1,localhost"
    port = 8766
    server = uvicorn.Server(uvicorn.Config(app_async, port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            httpx.get(f"{base}/docs", timeout=0.5)
            break
        except httpx.TransportError:
            time.sleep(0.2)

    async def five_at_once(path: str) -> float:
        async with httpx.AsyncClient(base_url=base, timeout=30) as ac:
            t = time.perf_counter()
            await asyncio.gather(*(ac.get(path) for _ in range(5)))
            return time.perf_counter() - t

    for path in ["/credit-check/sync", "/credit-check/bad", "/credit-check/good"]:
        print(f"{path:<20} 5 requests ek saath: {asyncio.run(five_at_once(path)):.2f}s")
    server.should_exit = True
    thread.join(timeout=5)


# =============================================================================
# 11. SETTINGS (.env) + LIFESPAN + DOOSRI API KO CALL KARNA
# =============================================================================
# Settings (pydantic-settings):
#   - Values .env file / environment variables se aati hain, type ke saath
#   - SecretStr: print/log karo to '**********', asli value sirf .get_secret_value() se
#   - .env git mein NAHI jati
# Lifespan:
#   - App SHURU hote waqt ek baar (shared httpx.AsyncClient, model load, DB connect)
#   - App BAND hote waqt saaf karna (connections close)
# Doosri API (yahan nakli "credit bureau") ki ghalti ka tarjuma:
#   - timeout -> 504 | pohanch nahi saka / upstream 5xx -> 502 | upstream 404 -> 404
# Tests mein asli API call nahi: httpx.MockTransport se nakli API + dependency_overrides
#
# Optional .env (isi folder mein), na ho to neeche wali default values chalein gi:
#   CREDIT_API_URL=https://credit-bureau.example
#   CREDIT_API_KEY=sk-real-key
#   REQUEST_TIMEOUT=3

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_name: str = "Loan API"
    credit_api_url: str = "https://credit-bureau.example"
    credit_api_key: SecretStr = SecretStr("sk-demo-key-123")
    request_timeout: float = 3


settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(
        base_url=settings.credit_api_url, timeout=settings.request_timeout,
        headers={"Authorization": f"Bearer {settings.credit_api_key.get_secret_value()}"})
    logger.info("Startup: shared HTTP client tayyar")
    yield
    await app.state.http.aclose()
    logger.info("Shutdown: connections band")


app_settings = FastAPI(title=settings.app_name, lifespan=lifespan)


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http


@app_settings.get("/credit-score/{customer_id}")
async def credit_score(customer_id: str, http: Annotated[httpx.AsyncClient, Depends(get_http)]):
    try:
        r = await http.get(f"/scores/{customer_id}")
    except httpx.TimeoutException:
        raise HTTPException(504, "Credit bureau ne waqt par jawab nahi diya")
    except httpx.TransportError:
        raise HTTPException(502, "Credit bureau tak pohanch nahi sake")
    if r.status_code == 404:
        raise HTTPException(404, "Credit record nahi mila")
    if r.is_error:
        raise HTTPException(502, "Credit bureau ne ghalat jawab diya")
    return {"customer_id": customer_id, "credit_score": r.json()["score"], "source": "credit-bureau"}


def fake_credit_bureau(request: httpx.Request) -> httpx.Response:
    """Nakli credit bureau API (tests/demo ke liye)."""
    scores = {"/scores/101": 720, "/scores/102": 580}
    if request.url.path == "/scores/103":
        raise httpx.ReadTimeout("slow", request=request)
    if request.url.path in scores:
        return httpx.Response(200, json={"score": scores[request.url.path]})
    if request.url.path == "/scores/104":
        return httpx.Response(500)
    return httpx.Response(404)


def demo_11_settings_lifespan():
    print(settings)                                      # credit_api_key: '**********'
    print("Asli key (sirf zaroorat par):", settings.credit_api_key.get_secret_value()[:7] + "...")

    app_settings.dependency_overrides[get_http] = lambda: httpx.AsyncClient(
        transport=httpx.MockTransport(fake_credit_bureau), base_url="http://mock")
    with TestClient(app_settings) as tc:                  # `with` -> lifespan chalta hai
        for cid in ["101", "102", "103", "104", "999"]:
            r = tc.get(f"/credit-score/{cid}")
            print(r.status_code, r.json())
    app_settings.dependency_overrides.clear()


# =============================================================================
# 12. MIDDLEWARE + CORS
# =============================================================================
# Middleware = har request se PEHLE aur BAAD chalne wala code:
#   Request -> [timer shuru, request id] -> endpoint -> [time likho, header lagao] -> Response
#   Kaam: request ID, timing, logging, rate limiting
# CORS (sirf BROWSERS par lagu, Python/curl par nahi):
#   myloanapp.example ka JavaScript aap ki API call kare to browser jawab tab hi
#   dikhaye ga jab server Access-Control-Allow-Origin se ijazat de. `*` production mein nahi.

app_middleware = FastAPI(title="12. Middleware + CORS")
app_middleware.add_middleware(CORSMiddleware, allow_origins=["https://myloanapp.example"],
                              allow_methods=["GET", "POST"], allow_headers=["*"])


def add_request_context(app: FastAPI) -> None:
    """Request ID + timing middleware (concept 16 mein dobara use hoga)."""

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:8]
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Process-Time-ms"] = f"{ms:.1f}"
        logger.info("%s %s -> %s (%.1fms) rid=%s", request.method, request.url.path,
                    response.status_code, ms, request.state.request_id)
        return response


add_request_context(app_middleware)


@app_middleware.get("/risk-profile/{customer_id}")
async def mw_risk_profile(customer_id: str):
    await asyncio.sleep(0.05)
    if customer_id not in CUSTOMERS:
        raise HTTPException(404, "Customer not found")
    return CUSTOMERS[customer_id]


def demo_12_middleware():
    tc = TestClient(app_middleware)
    r = tc.get("/risk-profile/101")
    print({k: v for k, v in r.headers.items() if k.startswith("x-")})
    r = tc.get("/risk-profile/101", headers={"Origin": "https://myloanapp.example"})
    print("Apni website ->", r.headers.get("access-control-allow-origin"))
    r = tc.get("/risk-profile/101", headers={"Origin": "https://hacker.example"})
    print("Ghair website ->", r.headers.get("access-control-allow-origin"), "(browser block kar de ga)")


# =============================================================================
# 13. WEBHOOK + BACKGROUND TASKS (WhatsApp jaisa)
# =============================================================================
# Webhook = DOOSRI service aap ke server ko call karti hai (naya WhatsApp message,
# payment, Shopify order). 4 cheezein zaroori:
#   1. Verify (GET): setup par hub.challenge wapas karo, agar verify token sahi ho
#   2. Signature: X-Hub-Signature-256 = body ka HMAC-SHA256 (app secret se).
#      Is se pata chalta hai request WAQAI WhatsApp se aayi
#   3. Dedupe: same message_id dobara aaye (retry) to ignore
#   4. Jaldi 200: lamba kaam (LLM) BackgroundTasks mein, warna sender retry kare ga
# hmac.compare_digest (== nahi) -> timing attack se bachao
# BackgroundTasks restart par kaam kho deta hai. Production: Redis/Celery queue.

app_webhook = FastAPI(title="13. Webhook")
VERIFY_TOKEN = "my-verify-token"          # asal mein .env se
APP_SECRET = "whatsapp-app-secret"        # asal mein .env se
processed_ids: set[str] = set()
outbox: list[str] = []


class IncomingMessage(BaseModel):
    message_id: str
    from_phone: str
    text: str


@app_webhook.get("/webhooks/whatsapp", response_class=PlainTextResponse)
def verify_webhook(mode: Annotated[str, Query(alias="hub.mode")],
                   token: Annotated[str, Query(alias="hub.verify_token")],
                   challenge: Annotated[str, Query(alias="hub.challenge")]):
    if mode == "subscribe" and hmac.compare_digest(token, VERIFY_TOKEN):
        return challenge
    raise HTTPException(403, "Verify token ghalat")


def reply_to_customer(msg: IncomingMessage):
    time.sleep(0.2)                        # LLM ka kaam (response jaane ke BAAD)
    outbox.append(f"-> {msg.from_phone}: Aap ki loan request mil gayi ('{msg.text}')")


@app_webhook.post("/webhooks/whatsapp")
async def receive_webhook(request: Request, background: BackgroundTasks,
                          x_hub_signature_256: Annotated[str | None, Header()] = None):
    raw = await request.body()
    expected = "sha256=" + hmac.new(APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    if not x_hub_signature_256 or not hmac.compare_digest(expected, x_hub_signature_256):
        raise HTTPException(401, "Signature ghalat")
    msg = IncomingMessage.model_validate_json(raw)
    if msg.message_id in processed_ids:
        return {"status": "duplicate_ignored"}
    processed_ids.add(msg.message_id)
    background.add_task(reply_to_customer, msg)
    return {"status": "received"}


def signed(payload: dict, secret: str = APP_SECRET) -> tuple[bytes, dict]:
    raw = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return raw, {"X-Hub-Signature-256": sig, "Content-Type": "application/json"}


def demo_13_webhook():
    processed_ids.clear()
    outbox.clear()
    tc = TestClient(app_webhook)
    print("Verify      :", tc.get("/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "777"}).text)
    print("Ghalat token:", tc.get("/webhooks/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "x", "hub.challenge": "1"}).status_code)
    raw, hdrs = signed({"message_id": "wamid.001", "from_phone": "923001234567", "text": "Mera loan status?"})
    print("Pehli baar  :", tc.post("/webhooks/whatsapp", content=raw, headers=hdrs).json())
    print("Retry (same):", tc.post("/webhooks/whatsapp", content=raw, headers=hdrs).json())
    raw2, bad = signed({"message_id": "wamid.002", "from_phone": "92300", "text": "hack"}, secret="hacker")
    print("Nakli       :", tc.post("/webhooks/whatsapp", content=raw2, headers=bad).status_code)
    print("Outbox      :", outbox, "<- sirf EK reply")


# =============================================================================
# 14. STREAMING RESPONSE (ChatGPT jaisa token by token)
# =============================================================================
# - Generator `yield` karta hai, StreamingResponse har tukra foran bhejta hai
# - Format: Server-Sent Events (SSE): har tukra "data: ...\n\n", aakhir mein [DONE]
# - media_type="text/event-stream"
# - User ko poore jawab ka intezar nahi karna parta

app_stream = FastAPI(title="14. Streaming")


async def explain_decision_tokens(data: ValidLoanApplication):
    decision = validated_predict(data)["decision"]
    reason = ("income acha hai aur job stable hai" if decision == "Approved"
              else "income 50000 se kam hai ya job 2 saal se kam hai")
    for word in f"Aap ki loan application {decision} hai kyun ke {reason}.".split():
        await asyncio.sleep(0.05)           # asal mein: async for chunk in llm.stream(...)
        yield f"data: {json.dumps({'token': word})}\n\n"
    yield "data: [DONE]\n\n"


@app_stream.post("/loans/explain")
async def explain_loan(data: ValidLoanApplication):
    return StreamingResponse(explain_decision_tokens(data), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})


def demo_14_streaming():
    body = {"age": 30, "income": 80000, "loan_amount": 200000, "employment_year": 5}
    with TestClient(app_stream).stream("POST", "/loans/explain", json=body) as r:
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                print(json.loads(line[6:])["token"], end=" ", flush=True)
    print()


# =============================================================================
# 15. TESTING (TestClient + pytest)
# =============================================================================
# - TestClient app ko BINA server ke call karta hai (API httpx jaisi). Upar ke saare
#   demos isi se chal rahe hain.
# - pytest: `test_` se shuru hone wale functions + assert. Chalayein:
#       python -m pytest 11_fastapi.py -v
#   (asal project mein ye tests/ folder mein alag files mein hote hain)
# - Doosri API/LLM ko asli call nahi: dependency_overrides / MockTransport (concept 8, 11)

def test_get_requires_customer_id():
    tc = TestClient(app_get)
    assert tc.get("/customer").status_code == 422
    assert tc.get("/customer?customer_id=101").json()["customer_id"] == 101


def test_loan_rules():
    tc = TestClient(app_validation)
    good = {"age": 30, "income": 80000, "loan_amount": 200000, "employment_year": 5}
    assert tc.post("/predict", json=good).json()["decision"] == "Approved"
    assert tc.post("/predict", json={**good, "employment_year": 1}).json()["decision"] == "Rejected"
    assert tc.post("/predict", json={**good, "age": 15}).status_code == 422


def test_missing_student_is_404_not_200():
    tc = TestClient(app_errors)
    r = tc.get("/students/s999")
    assert r.status_code == 404
    assert r.json()["error"]["message"] == "Student not found"


def test_password_never_returned():
    registered.clear()
    tc = TestClient(app_response)
    r = tc.post("/students", json={"student_id": "s009", "name": "Zara", "marks": 20, "major": "AI", "password": "secret123"})
    assert r.status_code == 201
    assert "password" not in r.json()


def test_manager_only_delete():
    tc = TestClient(app_deps)
    assert tc.delete("/customers/101").status_code == 401
    assert tc.delete("/customers/101", headers={"X-API-Key": "officer-key"}).status_code == 403
    assert tc.delete("/customers/101", headers={"X-API-Key": "manager-key"}).status_code == 204


def test_credit_score_upstream_errors():
    app_settings.dependency_overrides[get_http] = lambda: httpx.AsyncClient(
        transport=httpx.MockTransport(fake_credit_bureau), base_url="http://mock")
    with TestClient(app_settings) as tc:
        assert tc.get("/credit-score/101").json()["credit_score"] == 720
        assert tc.get("/credit-score/103").status_code == 504
        assert tc.get("/credit-score/104").status_code == 502
    app_settings.dependency_overrides.clear()


def demo_15_testing():
    tests = [test_get_requires_customer_id, test_loan_rules, test_missing_student_is_404_not_200,
             test_password_never_returned, test_manager_only_delete, test_credit_score_upstream_errors]
    for t in tests:
        t()
        print("PASSED", t.__name__)
    print("\nYahi tests pytest se:  python -m pytest 11_fastapi.py -v")


# =============================================================================
# 16. SAB KUCH EK APP MEIN (asli project jaisa)
# =============================================================================
# Ek hi `app`: lifespan + CORS + request id middleware + error handlers + routers.
# Chalayein:  uvicorn 11_fastapi:app --reload   ->   http://127.0.0.1:8000/docs
# Asli project mein ye sab alag files mein hota hai (zip ka part_h_store_api dekhein):
#   app/main.py, app/config.py, app/routers/*.py, app/deps.py, tests/
#
# Production checklist (zip: part_g_fastapi/NOTES.md G.14):
#   --reload nahi, --workers 4 | HTTPS | secrets .env mein | har external call par
#   timeout + retry | ek jaisa error format | logging (secrets mask) | GET /health |
#   rate limiting | input max_length | CORS sirf apne domains | tests CI mein

app = FastAPI(title="Loan & Student API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["https://myloanapp.example"],
                   allow_methods=["GET", "POST"], allow_headers=["*"])
add_request_context(app)
add_error_handlers(app)
for _r in (customers_router, loans_router, students_router):
    app.include_router(_r, prefix="/v1")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "version": app.version}


def demo_16_full_app():
    with TestClient(app, raise_server_exceptions=False) as tc:
        r = tc.get("/health")
        print(r.status_code, r.json(), "| request id:", r.headers["x-request-id"])
        print(tc.get("/v1/customers/101", headers={"X-API-Key": "officer-key"}).json())
        print(tc.get("/v1/customers/101").json())
        print(tc.get("/v1/students/s999").json())
        r = tc.post("/v1/loans/predict", json={"age": 15, "income": 0, "loan_amount": 1, "employment_year": 1})
        print(r.status_code, r.json())


# =============================================================================
# RUNNER: python 11_fastapi.py [concept numbers]
# =============================================================================
DEMOS = {
    1: ("GET method", demo_1_get),
    2: ("POST method + BaseModel", demo_2_post),
    3: ("Path parameter", demo_3_path),
    4: ("Query parameter", demo_4_query),
    5: ("Validation", demo_5_validation),
    6: ("Response model + status codes", demo_6_response_model),
    7: ("Exception handling", demo_7_errors),
    8: ("Dependency Injection", demo_8_dependencies),
    9: ("APIRouter", demo_9_routers),
    10: ("Sync vs Async (thora waqt lagay ga)", demo_10_sync_async),
    11: ("Settings + Lifespan + doosri API", demo_11_settings_lifespan),
    12: ("Middleware + CORS", demo_12_middleware),
    13: ("Webhook + Background tasks", demo_13_webhook),
    14: ("Streaming", demo_14_streaming),
    15: ("Testing", demo_15_testing),
    16: ("Sab kuch ek app mein", demo_16_full_app),
}

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    for noisy in ("httpx", "httpx2", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    chosen = [int(a) for a in sys.argv[1:]] or list(DEMOS)
    for n in chosen:
        name, fn = DEMOS[n]
        heading(f"{n}. {name}")
        fn()
