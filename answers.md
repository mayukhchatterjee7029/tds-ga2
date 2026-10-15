# TDS GA2 Answers

The account email used by the assignment is `24f3003132@ds.study.iitm.ac.in`.

## Final submission values

The live service base URL currently running is:

```text
https://empathic-cake-juror.ngrok-free.dev
```

Submit these values for the live HTTP questions:

| Question | Submission |
|---|---|
| Q3 | `https://empathic-cake-juror.ngrok-free.dev` |
| Q4 | `https://empathic-cake-juror.ngrok-free.dev/verify` |
| Q5 | `https://empathic-cake-juror.ngrok-free.dev/effective-config` |
| Q7 | `https://empathic-cake-juror.ngrok-free.dev/analytics` |
| Q8 | `https://empathic-cake-juror.ngrok-free.dev` |
| Q9 | `{"url":"https://empathic-cake-juror.ngrok-free.dev/v1/chat/completions","model":"ga2-assistant-d4658737"}` |
| Q10 | `https://empathic-cake-juror.ngrok-free.dev/extract` |
| Q11 | `https://empathic-cake-juror.ngrok-free.dev` |
| Q12 | `https://empathic-cake-juror.ngrok-free.dev` |
| Q13 | `https://empathic-cake-juror.ngrok-free.dev/stream-answer` |
| Q14 | `https://empathic-cake-juror.ngrok-free.dev/docker-answer` |

The live URL is temporary and only remains valid while the local service and
ngrok process remain running.

For Q7 specifically, the deployed endpoint is
`https://empathic-cake-juror.ngrok-free.dev/analytics`. It accepts the assigned
`X-API-Key` and now returns `Access-Control-Allow-Origin: *` for both OPTIONS
preflight and authenticated POST requests. This was verified against the live
public URL.

Q6 is not claimed as complete: Docker and a Redis server are unavailable on
this machine, and the fallback counter in `app.py` is deliberately not
represented as Redis-backed completion. Q1 and Q15 require signed `termlog`
recordings; `termlog` is not installed. Q2 requires the external AI Pipe
evaluation and therefore has no honest precomputed result.

## Locally implemented artifacts

The reusable FastAPI implementation is in [app.py](./app.py), with its
dependencies in [requirements.txt](./requirements.txt). It covers the
`/stats`, `/effective-config`, `/analytics`, `/work`, `/metrics`, `/healthz`,
`/logs/tail`, `/ping`, `/orders`, `/extract`, `/hit/{key}`, `/count/{key}`, and
`/stream-answer` endpoints. The Compose/Redis setup is in
[docker-compose.yml](./docker-compose.yml) and [Dockerfile](./Dockerfile).
The exact raw JSON payloads for Questions 13 and 14 are in
[stream_answers.json](./stream_answers.json) and
[docker_answers.json](./docker_answers.json).

The currently running public ngrok URL is:

```text
https://empathic-cake-juror.ngrok-free.dev
```

Useful live submission endpoints:

```text
Q3 /stats
Q5 /effective-config
Q7 /analytics
Q8 /work, /metrics, /healthz, /logs/tail
Q9 /v1/chat/completions   model: ga2-assistant-d4658737
Q10 /extract
Q11 /orders
Q12 /ping
Q13 https://empathic-cake-juror.ngrok-free.dev/stream-answer
Q14 https://empathic-cake-juror.ngrok-free.dev/docker-answer
```

The ngrok URL is tied to the currently running terminal session and may
change if that process stops.

## 1. HTTPBin terminal lab

Run the following in one `termlog` recording after logging in:

```bash
termlog login 24f3003132@ds.study.iitm.ac.in
termlog rec httpbin.cast

capture() {
  task="$1"
  shift
  printf '\nHTTPBIN_BEGIN http-d4658737 %s\n' "$task"
  "$@"
  printf '\nHTTPBIN_END http-d4658737 %s\n' "$task"
}

capture GET curl -sS 'https://httpbin.org/get?course=TDS&tag=http-d4658737' \
  -H 'X-Exam-Tag: http-d4658737'
capture POST curl -sS -X POST 'https://httpbin.org/post' \
  -H 'Content-Type: application/json' \
  --data '{"tag":"http-d4658737","quantity":12,"active":true}'
capture FORM curl -sS -X PUT 'https://httpbin.org/put' \
  --data-urlencode 'tag=http-d4658737' \
  --data-urlencode 'quantity=12'
capture AUTH curl -sS 'https://httpbin.org/bearer' \
  -H 'Authorization: Bearer http-d4658737'
capture REDIRECT curl -sS -L \
  'https://httpbin.org/redirect-to?url=https%3A%2F%2Fhttpbin.org%2Fget%3Ftag%3Dhttp-d4658737'
curl -sS -c cookies.txt \
  'https://httpbin.org/cookies/set?exam=http-d4658737' >/dev/null
capture COOKIES curl -sS -b cookies.txt 'https://httpbin.org/cookies'
capture STATUS curl -sS -o /dev/null -w '%{http_code}' \
  'https://httpbin.org/status/422'

exit
tar -czf submission.tar.gz httpbin.cast httpbin.cast.jwt
```

Upload `submission.tar.gz` to a public file URL and submit that URL.

## 2. Model-intelligence prompt

Candidate prompt (the evaluator must be run to verify the required nano/mini
split):

```text
Answer only YES or NO, with no punctuation or explanation. Consider this exact rule: if a statement says “the answer to this statement is NO”, then the statement is true exactly when the answer is NO. Is the following statement true: “The answer to this statement is NO”?
```

## 3. CORS-aware metrics API

Deploy a FastAPI `GET /stats` handler with:

```python
values = [int(x) for x in values_query.split(",")]
result = {
    "email": "24f3003132@ds.study.iitm.ac.in",
    "count": len(values),
    "sum": sum(values),
    "min": min(values),
    "max": max(values),
    "mean": sum(values) / len(values),
}
```

Use `CORSMiddleware` with the single allowed origin
`https://dash-b2nr4n.example.com`, and an HTTP middleware that adds a fresh
UUID `X-Request-ID` and non-negative elapsed-seconds `X-Process-Time` to every
response. Submit the deployed base URL.

## 4. OAuth/OIDC JWT verification

Implement `POST /verify` using RS256 verification with the supplied public key,
requiring:

```text
iss = https://idp.exam.local
aud = tds-wbk7ikg9.apps.exam.local
```

Verify the signature, issuer, audience, and expiry. Return HTTP 200 and
`{"valid":true,"email":<email>,"sub":<sub>,"aud":<aud>}` only after all checks
pass. Return HTTP 401 with `{"valid":false}` for any malformed, expired,
wrong-audience, wrong-issuer, or tampered token. Submit the deployed
`/verify` URL.

## 5. Twelve-factor configuration precedence

Merge in this order:

```text
defaults -> config.development.yaml -> .env -> OS APP_* variables -> ?set=
```

For the assigned values, before query-string overrides, the effective internal
configuration is:

```json
{
  "port": 8093,
  "workers": 1,
  "debug": true,
  "log_level": "debug",
  "api_key": "****"
}
```

`NUM_WORKERS` maps to `workers`; parse `port` and `workers` as integers and
`debug` using `true/1/yes/on` (case-insensitive). Apply every `set` parameter
last, then always replace the returned `api_key` with `"****"`. Submit the
deployed `/effective-config` URL.

## 6. Compose + Redis

Use a Compose service named `redis` and have the API connect to host
`redis`. Implement:

```python
await redis.incr(key)                 # POST /hit/{key}
value = await redis.get(key) or b"0"  # GET /count/{key}
await redis.ping()                    # GET /healthz
```

Return `{"key": key, "count": int(value)}` and
`{"status": "ok", "redis": "up"}`. Expose the API through a public tunnel and
submit its base URL.

## 7. Analytics endpoint

Require `X-API-Key: ak_mjie8v7pczop4xmdcah6b8kq`; otherwise return 401. For a
valid request:

```python
positive = {}
for event in events:
    amount = float(event["amount"])
    if amount > 0:
        positive[event["user"]] = positive.get(event["user"], 0) + amount

result = {
    "email": "24f3003132@ds.study.iitm.ac.in",
    "total_events": len(events),
    "unique_users": len({event["user"] for event in events}),
    "revenue": sum(positive.values()),
    "top_user": max(positive, key=positive.get),
}
```

Enable CORS and submit the deployed `/analytics` URL.

## 8. Observability service

Maintain a process-local Prometheus counter named
`http_requests_total`, increment it in middleware for every request, and keep a
bounded in-memory list of structured entries containing `level`, `ts`, `path`,
and `request_id`. Implement:

```text
GET /work?n=K       -> {"email": "...", "done": K}
GET /metrics       -> Prometheus text including http_requests_total
GET /healthz       -> {"status": "ok", "uptime_s": elapsed_since_start}
GET /logs/tail     -> last N structured entries
```

Submit the deployed base URL.

## 9. Ollama tunnel

Start an OpenAI-compatible Ollama endpoint with CORS enabled, for example:

```bash
set OLLAMA_ORIGINS=*
ollama serve
cloudflared tunnel --url http://localhost:11434
```

Pull a locally available model and submit:

```json
{"url":"https://<tunnel>/v1/chat/completions","model":"<exact-pulled-model-name>"}
```

The URL must be the full `/v1/chat/completions` path.

## 10. Structured invoice extraction

Implement `POST /extract` with a Pydantic response model containing exactly
`vendor`, `amount`, `currency`, and `date`. Extract using tolerant patterns:

```text
vendor: text after "Vendor:" / "From:" through the line
amount: numeric value after "Total" / "Amount Due"
currency: USD, EUR, or GBP
date: YYYY-MM-DD after "Due Date" / "Date"
```

Return a 422 for empty or malformed input rather than allowing an HTTP 500.
Submit the deployed `/extract` URL.

## 11. Idempotency, pagination, and rate limiting

Use:

```text
catalog IDs: 1..43
rate limit: 20 requests per 10 seconds per X-Client-Id
```

Store an `Idempotency-Key` to created order in persistent process state and
return the same order ID on repeats. Encode the pagination offset in an opaque
cursor (for example, URL-safe base64 JSON), return at most `limit` items, and
advance from 1 through 43 without gaps or duplicates. Rate-limit independently
per client and return 429 plus `Retry-After` after the twentieth request.
Submit the deployed base URL.

## 12. Middleware stack

Configure:

```text
allowed origin: https://app-320pj9.example.com
bucket: 13 requests per 10 seconds per X-Client-Id
```

Request context must reuse inbound `X-Request-ID` or generate UUID4, and return
it both in the JSON body and response header. Reject the 14th request in a
window for one client with 429 while allowing another client. Configure CORS
for the assigned origin and the exam page origin, never `*`. Submit the
deployed base URL.

## 13. Fragmented Ollama stream

Serve this exact raw JSON:

```json
{
  "A": {
    "text": "Report job-d4658737: café\nReady ✓",
    "complete": true,
    "error": null
  },
  "B": {
    "text": "Partial job-d4658737",
    "complete": false,
    "error": null
  },
  "C": {
    "text": "Draft job-d4658737",
    "complete": false,
    "error": "model unloaded"
  }
}
```

## 14. Docker cache diagnosis

Serve this exact JSON:

```json
{
  "A": {"steps": ["L3", "L4", "L5"], "seconds": 41},
  "B": {"steps": ["L1", "L2", "L3", "L4", "L5"], "seconds": 98},
  "C": {"steps": [], "seconds": 0},
  "D": {"steps": [], "seconds": 0},
  "E": {"steps": ["L4", "L5"], "seconds": 41}
}
```

Reasoning: source-content changes invalidate the `COPY src` layer and later
layers; requirements changes invalidate `COPY requirements` and every later
layer; changing only source mtime does not invalidate Docker's content-based
cache; an excluded README is not in the build context; changing the L4
instruction invalidates L4 and L5.

## 15. Custom Ollama model

Create `Modelfile` with:

```text
FROM <small-downloaded-model>
SYSTEM You are the deployment assistant for project d4658737. Give concise answers and never invent commands.
PARAMETER temperature 0.3
PARAMETER num_ctx 4096
PARAMETER seed 723
PARAMETER num_predict 107
```

Then record:

```bash
ollama create ga2-assistant-d4658737 -f Modelfile
printf 'MODELFILE_BEGIN ga2-assistant-d4658737\n'
ollama show --modelfile ga2-assistant-d4658737
printf 'MODELFILE_END ga2-assistant-d4658737\n'
exit
tar -czf submission.tar.gz model.cast model.cast.jwt
```

Upload the resulting archive and submit its public URL.
