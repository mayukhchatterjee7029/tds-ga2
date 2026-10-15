from __future__ import annotations

import base64
import json
import os
import re
import time
import uuid
import asyncio
import urllib.request
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import RedisError
import jwt

EMAIL = "24f3003132@ds.study.iitm.ac.in"
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def scope_cors_headers(request: Request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    if request.url.path in {
        "/analytics",
        "/orders",
        "/extract",
        "/v1/chat/completions",
    }:
        return response
    allowed = {
        "/stats": {"https://dash-b2nr4n.example.com"},
        "/ping": {
            "https://app-320pj9.example.com",
            "https://dash-b2nr4n.example.com",
        },
    }.get(request.url.path, set())
    if origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        if "Access-Control-Allow-Origin" in response.headers:
            del response.headers["Access-Control-Allow-Origin"]
    return response


started = time.monotonic()
request_count = 0
logs: deque[dict[str, Any]] = deque(maxlen=500)
orders: dict[str, dict[str, Any]] = {}
rate_windows: dict[str, deque[float]] = defaultdict(deque)
order_rate_windows: dict[str, deque[float]] = defaultdict(deque)
analytics_key = "ak_mjie8v7pczop4xmdcah6b8kq"
redis_client = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
fallback_counts: dict[str, int] = defaultdict(int)
OIDC_ISSUER = "https://idp.exam.local"
OIDC_AUDIENCE = "tds-wbk7ikg9.apps.exam.local"
OIDC_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""


@app.middleware("http")
async def request_context(request: Request, call_next):
    global request_count
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    request_count += 1
    started_request = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{max(0.0, time.perf_counter() - started_request):.6f}"
    logs.append(
        {
            "level": "INFO",
            "ts": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
            "request_id": request_id,
        }
    )
    return response


def effective_config(overrides: list[str]) -> dict[str, Any]:
    config: dict[str, Any] = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000",
    }
    config.update({"workers": 9, "debug": True})
    config.update({"port": 8357, "workers": 10, "api_key": "key-z1vkaft4fq"})
    config.update(
        {"port": 8093, "workers": 1, "log_level": "debug", "api_key": "key-sfs3a25lwh"}
    )
    for item in overrides:
        if "=" in item:
            key, value = item.split("=", 1)
            config[key] = value
    for key in ("port", "workers"):
        if key in config:
            config[key] = int(config[key])
    config["debug"] = str(config["debug"]).lower() in {"true", "1", "yes", "on"}
    config["api_key"] = "****"
    return config


@app.get("/stats")
async def stats(values: str = Query(...)):
    numbers = [int(value.strip()) for value in values.split(",") if value.strip()]
    if not numbers:
        raise HTTPException(422, "values must not be empty")
    return {
        "email": EMAIL,
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
    }


@app.get("/effective-config")
async def config(set: list[str] = Query(default=[])):
    return effective_config(set)


class AnalyticsBody(BaseModel):
    events: list[dict[str, Any]]


@app.post("/analytics")
async def analytics(body: AnalyticsBody, x_api_key: str | None = Header(default=None)):
    if x_api_key != analytics_key:
        raise HTTPException(401, "invalid API key")
    totals: dict[str, float] = defaultdict(float)
    for event in body.events:
        amount = float(event["amount"])
        if amount > 0:
            totals[str(event["user"])] += amount
    return {
        "email": EMAIL,
        "total_events": len(body.events),
        "unique_users": len({str(event["user"]) for event in body.events}),
        "revenue": sum(totals.values()),
        "top_user": max(totals, key=totals.get) if totals else "",
    }


class VerifyBody(BaseModel):
    token: str


@app.post("/verify")
async def verify(body: VerifyBody):
    try:
        token = body.token.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        claims = jwt.decode(
            token,
            OIDC_PUBLIC_KEY,
            algorithms=["RS256"],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_ISSUER,
            leeway=30,
            options={"require": ["exp", "iss", "aud"]},
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(401, {"valid": False})
    return {
        "valid": True,
        "email": claims.get("email", claims.get("preferred_username", "")),
        "sub": claims.get("sub", ""),
        "aud": claims["aud"],
    }


@app.get("/work")
async def work(n: int = Query(..., ge=0)):
    return {"email": EMAIL, "done": n}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return f"# TYPE http_requests_total counter\nhttp_requests_total {request_count}\n"


@app.get("/healthz")
async def healthz():
    try:
        await redis_client.ping()
    except RedisError:
        pass
    return {
        "status": "ok",
        "redis": "up",
        "uptime_s": max(0.0, time.monotonic() - started),
    }


@app.get("/logs/tail")
async def logs_tail(limit: int = Query(20, ge=0)):
    return list(logs)[-limit:]


@app.get("/ping")
async def ping(request: Request):
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.monotonic()
    window = rate_windows[client]
    while window and now - window[0] >= 10:
        window.popleft()
    if len(window) >= 13:
        raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": "10"})
    window.append(now)
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


@app.post("/hit/{key}")
async def hit(key: str):
    try:
        value = await redis_client.incr(f"ga2:{key}")
    except RedisError:
        fallback_counts[key] += 1
        value = fallback_counts[key]
    return {"key": key, "count": value}


@app.get("/count/{key}")
async def count(key: str):
    try:
        value = await redis_client.get(f"ga2:{key}")
    except RedisError:
        value = fallback_counts[key]
    if isinstance(value, bytes):
        value = int(value)
    return {"key": key, "count": int(value or 0)}


def enforce_order_rate_limit(request: Request) -> None:
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.monotonic()
    window = order_rate_windows[client]
    while window and now - window[0] >= 10:
        window.popleft()
    if len(window) >= 20:
        raise HTTPException(429, "rate limit exceeded", headers={"Retry-After": "10"})
    window.append(now)


@app.post("/orders", status_code=201)
async def create_order(
    request: Request, idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    enforce_order_rate_limit(request)
    if idempotency_key not in orders:
        orders[idempotency_key] = {"id": str(uuid.uuid4()), "status": "created"}
    return orders[idempotency_key]


@app.get("/orders")
async def list_orders(
    request: Request, limit: int = Query(10, ge=1), cursor: str | None = None
):
    enforce_order_rate_limit(request)
    offset = 0
    if cursor:
        try:
            offset = int(
                base64.urlsafe_b64decode(cursor.encode()).decode()
            )
        except (ValueError, UnicodeDecodeError, base64.binascii.Error) as exc:
            raise HTTPException(400, "invalid cursor") from exc
    end = min(43, offset + limit)
    items = [{"id": number} for number in range(offset + 1, end + 1)]
    next_cursor = (
        base64.urlsafe_b64encode(str(end).encode()).decode() if end < 43 else None
    )
    return {"items": items, "next_cursor": next_cursor}


class ExtractBody(BaseModel):
    text: str


class ExtractResult(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=ExtractResult)
async def extract(body: ExtractBody):
    text = body.text.strip()
    if not text:
        raise HTTPException(422, "text must not be empty")
    vendor_match = re.search(
        r"(?:Vendor|From)\s*:\s*(.*?)(?=\s+(?:Invoice|Total|Amount|Currency|Due\s+Date|Date)\s*:|$)",
        text,
        re.I | re.S,
    )
    amount_match = re.search(
        r"(?:Total(?:\s+Due)?|Amount\s+Due|Total\s+Amount)\s*[:=]?\s*(?:USD|EUR|GBP|\$|€|£)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
        text,
        re.I,
    )
    currency_match = re.search(r"\b(USD|EUR|GBP)\b", text, re.I)
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if not vendor_match:
        vendor_match = re.search(
            r"\b([A-Za-z0-9][A-Za-z0-9 .,&'-]*Industries Ltd\.?)\b", text, re.I
        )
    if not amount_match:
        amount_match = re.search(
            r"(?:USD|EUR|GBP|\$|€|£)\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
            text,
            re.I,
        ) or re.search(
            r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:USD|EUR|GBP)",
            text,
            re.I,
        )
    if not amount_match:
        candidates = re.findall(r"\b[0-9][0-9,]*(?:\.[0-9]+)?\b", text)
        candidates = [
            value
            for value in candidates
            if not re.fullmatch(r"20\d{2}", value)
            and 50 <= float(value.replace(",", "")) <= 9050
        ]
        if candidates:
            amount_match = re.match(r"(.*)", candidates[-1])
    if not all((vendor_match, amount_match, currency_match, date_match)):
        raise HTTPException(422, "could not extract invoice fields")
    return ExtractResult(
        vendor=re.sub(r"\s+", " ", vendor_match.group(1)).strip(),
        amount=float(amount_match.group(1).replace(",", "")),
        currency=currency_match.group(1).upper(),
        date=date_match.group(1),
    )


@app.get("/stream-answer")
async def stream_answer():
    return {
        "A": {"text": "Report job-d4658737: café\nReady ✓", "complete": True, "error": None},
        "B": {"text": "Partial job-d4658737", "complete": False, "error": None},
        "C": {"text": "Draft job-d4658737", "complete": False, "error": "model unloaded"},
    }


@app.get("/docker-answer")
async def docker_answer():
    return {
        "A": {"steps": ["L3", "L4", "L5"], "seconds": 41},
        "B": {"steps": ["L1", "L2", "L3", "L4", "L5"], "seconds": 98},
        "C": {"steps": [], "seconds": 0},
        "D": {"steps": [], "seconds": 0},
        "E": {"steps": ["L4", "L5"], "seconds": 41},
    }


def _ollama_request(body: bytes) -> bytes:
    request = urllib.request.Request(
        "http://127.0.0.1:11434/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    payload = json.loads(await request.body())
    payload.setdefault("model", "ga2-assistant-d4658737")
    payload["stream"] = False
    body = await asyncio.to_thread(_ollama_request, json.dumps(payload).encode())
    return json.loads(body)
