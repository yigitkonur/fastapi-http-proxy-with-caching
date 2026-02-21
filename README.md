transparent HTTP forward proxy with Redis-backed response deduplication. point any HTTP client at it — n8n, Make, Zapier, curl, whatever — and identical upstream requests get served from cache. Redis is optional; without it, the proxy degrades to pass-through.

```bash
pip install -r requirements.txt
uvicorn main:app
```

[![python](https://img.shields.io/badge/python-3.11+-93450a.svg?style=flat-square)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-93450a.svg?style=flat-square)](https://fastapi.tiangolo.com/)
[![license](https://img.shields.io/badge/license-MIT-grey.svg?style=flat-square)](https://opensource.org/licenses/MIT)

---

## how it works

1. client sends a request to `/proxy?url=https://api.example.com/data`
2. proxy computes an MD5 hash over method + URL + filtered headers + body
3. cache hit → return stored response, never touch upstream
4. cache miss → forward request, store response in Redis with TTL, return to client

only responses with `status_code < 400` get cached. errors always pass through.

## what it does

- **MD5 deduplication** — normalized request signature strips volatile headers (`x-request-id`, `date`, `authorization`, `cf-ray`, etc.) so logically identical requests share a cache key
- **Redis optional** — if Redis is unreachable on startup, logs a warning and runs as a pure proxy
- **binary handling** — non-text responses get base64-wrapped in a JSON envelope automatically
- **per-request TTL override** — `?cache_ttl=300` on any request
- **cache bypass** — `?bypass_cache=true` to force upstream hit
- **health + stats endpoints** — `/health`, `/cache/stats`, `DELETE /cache`
- **connection pooling** — single long-lived `httpx.AsyncClient` with 100 max connections

## install

### local

```bash
git clone https://github.com/yigitkonur/proxy-http-cache.git
cd proxy-http-cache

pip install -r requirements.txt
cp .env.example .env
# edit .env — set REDIS_URL at minimum

uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t proxy-http-cache .
docker run -p 8000:8000 \
  -e REDIS_URL=redis://your-redis:6379/0 \
  proxy-http-cache
```

multi-stage build, runs as non-root `appuser`, built-in healthcheck.

## usage

### proxy a request

```bash
# GET
curl "http://localhost:8000/proxy?url=https://api.example.com/data"

# POST with body
curl -X POST "http://localhost:8000/proxy?url=https://api.example.com/submit" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# bypass cache
curl "http://localhost:8000/proxy?url=https://api.example.com/data&bypass_cache=true"

# custom TTL (seconds)
curl "http://localhost:8000/proxy?url=https://api.example.com/data&cache_ttl=300"
```

supports GET, POST, PUT, DELETE, PATCH.

### response

```json
{
  "success": true,
  "cached": true,
  "cache_key": "proxy:cache:a1b2c3d4e5f6...",
  "status_code": 200,
  "data": { ... }
}
```

### health check

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "redis_connected": true,
  "cache_stats": { "total_keys": 42 }
}
```

`status` is `"degraded"` when Redis is disconnected.

### cache management

```bash
# stats
curl http://localhost:8000/cache/stats

# clear all cached entries
curl -X DELETE http://localhost:8000/cache
```

### legacy endpoint

`POST /webhook-test/post-response?url=...` — same behavior as `/proxy`, kept for backward compatibility with existing n8n workflows.

## configuration

| variable | default | description |
|:---|:---|:---|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `CACHE_TTL_SECONDS` | `3600` | default TTL. `0` = no expiry |
| `CACHE_PREFIX` | `proxy:cache:` | Redis key namespace |
| `PROXY_TIMEOUT_SECONDS` | `30.0` | upstream request timeout |
| `MAX_REQUEST_BODY_SIZE` | `10485760` | max inbound body (10 MB) |
| `EXCLUDED_HEADERS` | `host,content-length,connection,accept-encoding,transfer-encoding` | headers stripped before forwarding |
| `DEBUG` | `false` | enables auto-reload and debug logging |
| `HOST` | `0.0.0.0` | bind address |
| `PORT` | `8000` | bind port |

all configurable via `.env` file or environment variables.

## cache key algorithm

```
signature = {
  "method":   "POST",
  "url":      "https://...",
  "headers":  { sorted, volatile headers stripped },
  "body_md5": MD5(raw_body)
}

cache_key = CACHE_PREFIX + MD5(JSON(signature))
```

volatile headers excluded from hash: `x-request-id`, `x-correlation-id`, `date`, `authorization`, `x-forwarded-for`, `x-real-ip`, `cf-ray`, `cf-connecting-ip`. this means different auth tokens hitting the same endpoint share a cache entry — by design, for internal/trusted use.

## project structure

```
app/
  __init__.py         — package metadata (v2.0.0)
  main.py             — FastAPI app factory, lifespan, CORS, exception handler
  config.py           — pydantic settings, all env var definitions
  models.py           — request/response models
  dependencies.py     — service lifecycle, FastAPI DI providers
  routes/
    proxy.py          — /proxy endpoint + legacy /webhook-test
    health.py         — /health, /cache/stats, DELETE /cache
  services/
    cache.py          — Redis async client, MD5 key generation, get/set/clear
    proxy.py          — httpx async client, request forwarding, response parsing
main.py               — top-level entry point
Dockerfile            — multi-stage build (builder + production)
```

## error codes

| code | meaning |
|:---|:---|
| `200` | success (cached or fresh) |
| `400` | missing `url` parameter |
| `502` | upstream connection failed |
| `504` | upstream request timed out |

## license

MIT
