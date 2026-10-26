"""App factory: middleware, error handlers, routers sab yahan jurte hain.

Chalayein (part_h_store_api folder ke andar se):
    uvicorn app.main:app --reload --port 8767
"""
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.routers import chat, health, orders

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("store_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", app.title)       # yahan: DB connect, shared clients, model load
    yield
    logger.info("Shutting down")


def _error(request: Request, code: int, message: str, details=None) -> JSONResponse:
    body = {"error": {"code": code, "message": message,
                      "request_id": getattr(request.state, "request_id", None)}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=code, content=body)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=["GET", "POST"], allow_headers=["*"])

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:8]
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info("%s %s -> %s %.1fms rid=%s", request.method, request.url.path,
                    response.status_code, ms, request.state.request_id)
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        response = _error(request, exc.status_code, str(exc.detail))
        for k, v in (exc.headers or {}).items():
            response.headers[k] = v
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
        return _error(request, 422, "Validation failed", details)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        logger.exception("Unhandled error")
        return _error(request, 500, "Internal server error")

    for r in (health.router, orders.router, chat.router):
        app.include_router(r, prefix="/v1")
    return app


app = create_app()
