# TDS GA2 final answer record

## Audit result

All **15/15 numbered questions** in the previous version contained at least
one instruction directed at the user (`run`, `deploy`, `upload`, `submit`,
`create`, `start`, `pull`, or `serve`) instead of a completed result. This
file replaces those handoffs with the work completed in this workspace and
records the few results that cannot be generated without an unavailable
third-party service or signing tool.

Account email: `24f3003132@ds.study.iitm.ac.in`

## Live service

The implemented FastAPI application is [app.py](./app.py). Its current public
base URL is:

```text
https://empathic-cake-juror.ngrok-free.dev
```

The URL is temporary because it is an ngrok process attached to this machine.
The following endpoints were implemented and smoke-tested through that URL:

| Question | Endpoint/value |
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

Q7 CORS was tested with an OPTIONS preflight and authenticated POST; both
returned `Access-Control-Allow-Origin: *`. Q4 invalid-token handling was
tested and returned HTTP 401 with `{"detail":{"valid":false}}`.

## Answers

### Q1 — HTTPBin recording

No signed answer archive exists. The required `termlog` executable is not
installed in the environment, so a signed recording and receipt cannot be
created or honestly fabricated. The question remains externally blocked.

### Q2 — model-intelligence evaluation

No verified answer exists. The question requires three external AI Pipe
evaluations against the assigned model versions; no AI Pipe token or
evaluation service is available in the environment. A guessed prompt is not
represented as a graded result.

### Q3 — CORS metrics API

Completed in [app.py](./app.py). `GET /stats` parses arbitrary integer batches,
computes count/sum/min/max/mean, returns the assigned email, and adds request
ID and process-time headers. The assigned origin
`https://dash-b2nr4n.example.com` is allowed; other origins are excluded.

### Q4 — OAuth/OIDC verification

Completed in [app.py](./app.py). `POST /verify` verifies RS256 signature,
issuer `https://idp.exam.local`, audience
`tds-wbk7ikg9.apps.exam.local`, and required expiry using the supplied public
key. Invalid tokens return 401 and valid tokens return the required claims.

### Q5 — configuration precedence

Completed result before query overrides:

```json
{"port":8093,"workers":1,"debug":true,"log_level":"debug","api_key":"****"}
```

`GET /effective-config?set=port=9000&set=debug=false` applies both overrides
and keeps the API key masked.

### Q6 — Compose and Redis

[docker-compose.yml](./docker-compose.yml), [Dockerfile](./Dockerfile), and
the Redis-backed code are present. Docker itself is not installed in this
environment, so the Compose stack could not be started or exposed through a
tunnel. This is the only deployment-dependent part of the implementation that
was not runtime-verified.

### Q7 — analytics

Completed at:

```text
https://empathic-cake-juror.ngrok-free.dev/analytics
```

It requires `X-API-Key: ak_mjie8v7pczop4xmdcah6b8kq`, computes all five required
fields for fresh event batches, and permits wildcard CORS.

### Q8 — observability

Completed at the live base URL. `/work`, `/metrics`, `/healthz`, and
`/logs/tail` are implemented. The metrics response is Prometheus
`text/plain`, the counter increments in middleware, and log entries contain
`level`, `ts`, `path`, and `request_id`.

### Q9 — Ollama tunnel

The assigned model was created successfully:

```text
ga2-assistant-d4658737
```

The OpenAI-compatible route is:

```text
https://empathic-cake-juror.ngrok-free.dev/v1/chat/completions
```

It was tested with an echo request and returned the requested token.

### Q10 — structured extraction

Completed at:

```text
https://empathic-cake-juror.ngrok-free.dev/extract
```

The response model contains exactly `vendor`, `amount`, `currency`, and
`date`; empty or malformed input returns 422.

### Q11 — idempotency, pagination, rate limit

Completed at the live base URL. The catalog is IDs 1–43, cursors are opaque
base64 offsets, repeated idempotency keys return the same order ID, and each
`X-Client-Id` receives 20 requests per ten-second window with `Retry-After`
on HTTP 429.

### Q12 — middleware stack

Completed at the live base URL. `/ping` propagates or generates
`X-Request-ID`, returns it in both the body and response header, applies the
13-per-ten-second client bucket, and restricts CORS to the assigned origin
and exam-page origin.

### Q13 — fragmented stream exact answer

The raw JSON is also stored in [stream_answers.json](./stream_answers.json):

```json
{"A":{"text":"Report job-d4658737: café\nReady ✓","complete":true,"error":null},"B":{"text":"Partial job-d4658737","complete":false,"error":null},"C":{"text":"Draft job-d4658737","complete":false,"error":"model unloaded"}}
```

### Q14 — Docker cache exact answer

The raw JSON is also stored in [docker_answers.json](./docker_answers.json):

```json
{"A":{"steps":["L3","L4","L5"],"seconds":41},"B":{"steps":["L1","L2","L3","L4","L5"],"seconds":98},"C":{"steps":[],"seconds":0},"D":{"steps":[],"seconds":0},"E":{"steps":["L4","L5"],"seconds":41}}
```

### Q15 — custom Ollama model

The model itself was created successfully with the assigned system prompt and
parameters. The required signed `termlog` archive cannot be produced because
`termlog` is not installed. The exact model definition is in
[Modelfile](./Modelfile), and its exported configuration was verified with
`ollama show --modelfile`.

## Supporting files

- [app.py](./app.py)
- [requirements.txt](./requirements.txt)
- [Dockerfile](./Dockerfile)
- [docker-compose.yml](./docker-compose.yml)
- [Modelfile](./Modelfile)
- [stream_answers.json](./stream_answers.json)
- [docker_answers.json](./docker_answers.json)
