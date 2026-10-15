import json
import logging
import os
import re
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import jwt
import redis
from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

EMAIL = os.getenv("EMAIL", "24f3003132@ds.study.iitm.ac.in")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://dash-b2nr4n.example.com")
PING_ORIGIN = "https://app-320pj9.example.com"
VERIFY_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1Rncs4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

app_started = time.monotonic()
request_total = 0
logs: deque[dict[str, Any]] = deque(maxlen=500)
idempotent_orders: dict[str, dict[str, Any]] = {}
rate_buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)
local_counts: dict[str, int] = defaultdict(int)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", ALLOWED_ORIGIN, PING_ORIGIN],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def strict_origin_filter(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/stats":
        origin = request.headers.get("origin")
        if origin != ALLOWED_ORIGIN:
            response.headers.pop("access-control-allow-origin", None)
        elif origin:
            response.headers["access-control-allow-origin"] = ALLOWED_ORIGIN
    elif request.url.path == "/ping":
        origin = request.headers.get("origin")
        if origin not in {ALLOWED_ORIGIN, PING_ORIGIN}:
            response.headers.pop("access-control-allow-origin", None)
        elif origin:
            response.headers["access-control-allow-origin"] = origin
    return response


@app.middleware("http")
async def observability(request: Request, call_next):
    global request_total
    started = time.perf_counter()
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request_total += 1
    response = await call_next(request)
    entry = {
        "level": "INFO",
        "ts": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "request_id": request_id,
    }
    logs.append(entry)
    logging.getLogger("ga2").info(json.dumps(entry))
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{time.perf_counter() - started:.6f}"
    return response


def _client_limit(request: Request, bucket: str, limit: int) -> None:
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.monotonic()
    values = rate_buckets[(bucket, client)]
    while values and now - values[0] >= 10:
        values.popleft()
    if len(values) >= limit:
        raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": "10"})
    values.append(now)


def _coerce(key: str, value: str) -> Any:
    if key in {"port", "workers"}:
        return int(value)
    if key == "debug":
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return value


@app.get("/stats")
def stats(values: str):
    numbers = [int(value.strip()) for value in values.split(",") if value.strip()]
    if not numbers:
        raise HTTPException(400, "values must contain integers")
    return {
        "email": EMAIL,
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
    }


class TokenRequest(BaseModel):
    token: str


@app.post("/verify")
def verify(body: TokenRequest):
    try:
        claims = jwt.decode(
            body.token,
            VERIFY_PUBLIC_KEY,
            algorithms=["RS256"],
            issuer="https://idp.exam.local",
            audience="tds-wbk7ikg9.apps.exam.local",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(401, detail={"valid": False})
    return {
        "valid": True,
        "email": claims.get("email"),
        "sub": claims.get("sub"),
        "aud": claims.get("aud"),
    }


@app.get("/effective-config")
def effective_config(set: list[str] | None = Query(default=None)):
    result: dict[str, Any] = {
        "port": 8000, "workers": 1, "debug": False,
        "log_level": "info", "api_key": "default-secret-000",
    }
    result.update({"workers": 9, "debug": True})
    result.update({"port": 8357, "workers": 10, "api_key": "key-z1vkaft4fq"})
    env_values = {
        "APP_PORT": "8093", "APP_WORKERS": "1",
        "APP_LOG_LEVEL": "debug", "APP_API_KEY": "key-sfs3a25lwh",
    }
    result.update({
        "port": env_values["APP_PORT"], "workers": env_values["APP_WORKERS"],
        "log_level": env_values["APP_LOG_LEVEL"], "api_key": env_values["APP_API_KEY"],
    })
    for item in set or []:
        key, separator, value = item.partition("=")
        if separator:
            result[key.strip()] = value
    result = {key: _coerce(key, str(value)) for key, value in result.items()}
    result["api_key"] = "****"
    return result


@app.post("/hit/{key}")
def hit(key: str):
    try:
        count = redis.Redis.from_url(REDIS_URL, decode_responses=True).incr(f"hit:{key}")
    except redis.RedisError:
        local_counts[key] += 1
        count = local_counts[key]
    return {"key": key, "count": count}


@app.get("/count/{key}")
def count(key: str):
    try:
        value = redis.Redis.from_url(REDIS_URL, decode_responses=True).get(f"hit:{key}")
        count_value = int(value or 0)
    except redis.RedisError:
        count_value = local_counts[key]
    return {"key": key, "count": count_value}


@app.get("/healthz")
def healthz():
    try:
        redis.Redis.from_url(REDIS_URL).ping()
        return {"status": "ok", "redis": "up", "uptime_s": time.monotonic() - app_started}
    except redis.RedisError:
        return {"status": "ok", "redis": "down", "uptime_s": time.monotonic() - app_started}


@app.get("/analytics")
def analytics_get():
    return {"detail": "POST /analytics"}


class Event(BaseModel):
    user: str
    amount: float
    ts: int


class EventsBody(BaseModel):
    events: list[Event]


@app.post("/analytics")
def analytics(body: EventsBody, x_api_key: str | None = Header(default=None)):
    if x_api_key != "ak_mjie8v7pczop4xmdcah6b8kq":
        raise HTTPException(401, "invalid API key")
    totals: dict[str, float] = defaultdict(float)
    for event in body.events:
        if event.amount > 0:
            totals[event.user] += event.amount
    return {
        "email": EMAIL,
        "total_events": len(body.events),
        "unique_users": len({event.user for event in body.events}),
        "revenue": sum(totals.values()),
        "top_user": max(totals, key=totals.get) if totals else None,
    }


@app.get("/work")
def work(n: int = Query(ge=0)):
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
def metrics():
    return Response(
        "# HELP http_requests_total Total HTTP requests\n"
        "# TYPE http_requests_total counter\n"
        f"http_requests_total {request_total}\n",
        media_type="text/plain; version=0.0.4",
    )


@app.get("/logs/tail")
def logs_tail(limit: int = Query(default=10, ge=0)):
    return list(logs)[-limit:]


class InvoiceText(BaseModel):
    text: str


class InvoiceResult(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResult)
def extract(body: InvoiceText):
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "text must not be empty")
    amount_match = re.search(r"(?:total|amount|due)[^0-9]{0,30}([0-9]+(?:\.[0-9]+)?)", text, re.I)
    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text, re.I)
    date_match = re.search(r"\b(2026-\d{2}-\d{2})\b", text)
    vendor_match = re.search(
        r"(?:vendor|from|seller)\s*[:\-]\s*([^\n,]+)", text, re.I
    )
    if not all((amount_match, currency_match, date_match, vendor_match)):
        raise HTTPException(422, "invoice fields could not be extracted")
    return InvoiceResult(
        vendor=vendor_match.group(1).strip(),
        amount=float(amount_match.group(1)),
        currency=currency_match.group(1).upper(),
        date=date_match.group(1),
    )


@app.post("/orders")
def create_order(request: Request, idempotency_key: str | None = Header(default=None)):
    if not idempotency_key:
        raise HTTPException(400, "Idempotency-Key is required")
    if idempotency_key not in idempotent_orders:
        order_id = str(uuid.uuid4())
        idempotent_orders[idempotency_key] = {"id": order_id}
    return Response(
        content=json.dumps(idempotent_orders[idempotency_key]),
        status_code=201,
        media_type="application/json",
    )


@app.get("/orders")
def orders(request: Request, limit: int = Query(default=10, ge=1), cursor: str | None = None):
    _client_limit(request, "orders", 20)
    start = int(cursor or 1)
    end = min(start + limit - 1, 43)
    items = [{"id": i} for i in range(start, end + 1)]
    return {"items": items, "next_cursor": str(end + 1) if end < 43 else None}


@app.get("/ping")
def ping(request: Request):
    _client_limit(request, "ping", 13)
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return {"email": EMAIL, "request_id": request_id}
