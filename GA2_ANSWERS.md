# TDS GA2 Answer Sheet

Email used in the assignment: `24f3003132@ds.study.iitm.ac.in`

The deployable implementation is in [ga2_solution.py](./ga2_solution.py), with dependency and container files in [requirements.txt](./requirements.txt), [Dockerfile](./Dockerfile), and [docker-compose.yml](./docker-compose.yml).

## 1. HTTPBin terminal lab

Run these commands inside the `termlog` recording:

```bash
termlog login as 24f3003132@ds.study.iitm.ac.in
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

capture POST curl -sS 'https://httpbin.org/post' \
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
  'https://httpbin.org/cookies/set?exam=http-d4658737' > /dev/null
capture COOKIES curl -sS -b cookies.txt 'https://httpbin.org/cookies'

capture STATUS curl -sS -o /dev/null -w '%{http_code}' \
  'https://httpbin.org/status/422'

exit
tar -czf submission.tar.gz httpbin.cast httpbin.cast.jwt
```

Upload `submission.tar.gz` to a public file URL and submit that URL.

## 2. Model intelligence prompt

Submit the contents of [model-prompt.txt](./model-prompt.txt):

```text
Answer only YES or NO. Is the following statement true? "This statement is false."
```

This question is probabilistic because the page evaluates the prompt against two models. Check the result using the supplied AI Pipe token before relying on it.

## 3. CORS-aware metrics API

Deploy [ga2_solution.py](./ga2_solution.py) and submit the base URL. The implementation provides:

```text
GET /stats?values=1,2,3
```

Required assigned origin:

```text
https://dash-b2nr4n.example.com
```

Example local deployment:

```bash
uvicorn ga2_solution:app --host 0.0.0.0 --port 8000
```

## 4. OAuth/OIDC verification API

Submit the deployed URL:

```text
https://YOUR-HOST/verify
```

The implementation validates:

```text
Issuer:   https://idp.exam.local
Audience: tds-wbk7ikg9.apps.exam.local
Algorithm: RS256
```

The public key is embedded in [ga2_solution.py](./ga2_solution.py).

## 5. Configuration precedence API

Submit:

```text
https://YOUR-HOST/effective-config
```

The endpoint implements this precedence:

```text
defaults
  < config.development.yaml
  < .env
  < APP_* OS environment variables
  < repeated ?set=key=value CLI overrides
```

The API key is always returned as:

```json
"api_key": "****"
```

Example:

```text
/effective-config?set=port=9000&set=debug=true
```

## 6. Compose + Redis tunnel

Start the stack using [docker-compose.yml](./docker-compose.yml):

```bash
docker compose up --build
```

Expose port 8000:

```bash
cloudflared tunnel --url http://localhost:8000
```

Endpoints:

```text
GET  /healthz
POST /hit/{key}
GET  /count/{key}
```

Submit the generated public tunnel base URL.

## 7. Analytics API

Submit:

```text
https://YOUR-HOST/analytics
```

Required header:

```text
X-API-Key: ak_mjie8v7pczop4xmdcah6b8kq
```

The endpoint computes `total_events`, `unique_users`, positive-only `revenue`, and `top_user` dynamically.

## 8. Observability API

Submit the deployed base URL. Endpoints:

```text
GET /work?n=K
GET /metrics
GET /healthz
GET /logs/tail?limit=N
```

The live counter is:

```text
http_requests_total
```

## 9. Ollama tunnel

Run an OpenAI-compatible Ollama server and expose:

```text
/v1/chat/completions
```

Submit JSON in this format:

```json
{
  "url": "https://YOUR-TUNNEL/v1/chat/completions",
  "model": "YOUR-EXACT-OLLAMA-MODEL-NAME"
}
```

Set CORS before starting Ollama:

```bash
OLLAMA_ORIGINS=* ollama serve
```

## 10. Structured invoice extraction API

Submit:

```text
https://YOUR-HOST/extract
```

Request:

```json
{
  "text": "Vendor: Acme Industries Ltd. Total due: USD 1250.50. Due date: 2026-10-31"
}
```

Response shape:

```json
{
  "vendor": "Acme Industries Ltd.",
  "amount": 1250.50,
  "currency": "USD",
  "date": "2026-10-31"
}
```

## 11. Idempotency, pagination, and rate limiting

Submit:

```text
https://YOUR-HOST
```

Endpoints:

```text
POST /orders
GET  /orders?limit=10
GET  /orders?limit=10&cursor=...
```

Assigned values:

```text
Total orders: 43
Rate limit: 20 requests per 10 seconds
```

Creation requests must include:

```text
Idempotency-Key: any-stable-key
```

## 12. Middleware stack

Submit:

```text
https://YOUR-HOST
```

Endpoint:

```text
GET /ping
```

Assigned values:

```text
Allowed origin: https://app-320pj9.example.com
Rate limit: 13 requests per 10 seconds
```

The implementation supports `X-Request-ID` reuse/generation and independent `X-Client-Id` rate buckets.

## 13. LLM stream reassembly

The exact answer is in [stream-answer.json](./stream-answer.json):

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

Host this file as raw JSON and submit its public URL.

## 14. Docker build cache

The exact answer is in [docker-cache-answer.json](./docker-cache-answer.json):

```json
{
  "A": {"steps": ["L3", "L4", "L5"], "seconds": 41},
  "B": {"steps": ["L1", "L2", "L3", "L4", "L5"], "seconds": 98},
  "C": {"steps": [], "seconds": 0},
  "D": {"steps": [], "seconds": 0},
  "E": {"steps": ["L4", "L5"], "seconds": 41}
}
```

Host this file as raw JSON and submit its public URL.

## 15. Custom Ollama model

Create `Modelfile` during the recording:

```text
FROM YOUR_SMALL_BASE_MODEL

SYSTEM You are the deployment assistant for project d4658737. Give concise answers and never invent commands.

PARAMETER temperature 0.3
PARAMETER num_ctx 4096
PARAMETER seed 723
PARAMETER num_predict 107
```

Run:

```bash
termlog login as 24f3003132@ds.study.iitm.ac.in
termlog rec model.cast
ollama create ga2-assistant-d4658737 -f Modelfile
printf '\nMODELFILE_BEGIN ga2-assistant-d4658737\n'
ollama show --modelfile ga2-assistant-d4658737
printf 'MODELFILE_END ga2-assistant-d4658737\n'
exit
tar -czf submission.tar.gz model.cast model.cast.jwt
```

Upload the archive and submit its public URL.

## Local validation

```bash
python -m py_compile ga2_solution.py
docker compose up --build
```

