<h1 align="center">🚀 FastAPI Transparent Proxy 🚀</h1>
<h3 align="center">Stop paying for duplicate API calls. Start caching like a pro.</h3>

<p align="center">
  <strong>
    <em>The ultimate transparent HTTP proxy for no-code platforms. It sits between your automations and expensive APIs, caching responses based on MD5 hashes so identical requests return instantly.</em>
  </strong>
</p>

<p align="center">
  <!-- Package Info -->
  <a href="#"><img alt="python" src="https://img.shields.io/badge/python-3.10+-4D87E6.svg?style=flat-square"></a>
  <a href="#"><img alt="fastapi" src="https://img.shields.io/badge/FastAPI-0.109+-009688.svg?style=flat-square"></a>
  &nbsp;&nbsp;•&nbsp;&nbsp;
  <!-- Features -->
  <a href="#"><img alt="license" src="https://img.shields.io/badge/License-MIT-F9A825.svg?style=flat-square"></a>
  <a href="#"><img alt="platform" src="https://img.shields.io/badge/platform-macOS_|_Linux_|_Windows_|_Docker-2ED573.svg?style=flat-square"></a>
</p>

<p align="center">
  <img alt="zero config" src="https://img.shields.io/badge/⚙️_zero_config-works_without_redis-2ED573.svg?style=for-the-badge">
  <img alt="n8n ready" src="https://img.shields.io/badge/🔧_no--code_ready-n8n_|_Make_|_Zapier-2ED573.svg?style=for-the-badge">
</p>

<div align="center">

### 🧭 Quick Navigation

[**⚡ Get Started**](#-get-started-in-60-seconds) •
[**✨ Key Features**](#-feature-breakdown-the-secret-sauce) •
[**🎮 Usage & Examples**](#-usage-fire-and-forget) •
[**⚙️ Configuration**](#%EF%B8%8F-configuration) •
[**🆚 Why This Slaps**](#-why-this-slaps-other-methods)

</div>

---

**FastAPI Transparent Proxy** is the caching layer your no-code automations wish they had. Stop making the same API calls over and over. This proxy sits between your n8n/Make/Zapier workflows and expensive third-party APIs, returning cached responses for identical requests—saving bandwidth, reducing latency, and cutting your API bills.

<div align="center">
<table>
<tr>
<td align="center">
<h3>🧠</h3>
<b>MD5 Deduplication</b><br/>
<sub>Same request = same cache key</sub>
</td>
<td align="center">
<h3>⚡</h3>
<b>Sub-ms Response</b><br/>
<sub>Cache hits are instant</sub>
</td>
<td align="center">
<h3>🔌</h3>
<b>Zero Config</b><br/>
<sub>Works without Redis too</sub>
</td>
</tr>
</table>
</div>

How it slaps:
- **You:** Point your n8n HTTP Request node to this proxy
- **Proxy:** Hashes the request, checks cache, returns or forwards
- **Result:** First call hits the API, next 1000 identical calls return instantly
- **Your wallet:** 📈

---

## 💥 Why This Slaps Other Methods

Manually deduplicating API calls in no-code is a nightmare. This proxy makes other approaches look ancient.

<table align="center">
<tr>
<td align="center"><b>❌ The Old Way (Pain)</b></td>
<td align="center"><b>✅ The Proxy Way (Glory)</b></td>
</tr>
<tr>
<td>
<ol>
  <li>Build complex "check if already fetched" logic</li>
  <li>Store results in Airtable/Notion/Sheets</li>
  <li>Add branches: "if cached then skip"</li>
  <li>Debug why your workflow is 47 nodes</li>
  <li>Pay for 1000 duplicate API calls anyway</li>
</ol>
</td>
<td>
<ol>
  <li>Deploy this proxy (one command)</li>
  <li>Change your API URL to proxy URL</li>
  <li>Done. Caching is automatic.</li>
  <li>Watch your API costs drop 90%</li>
  <li>Go grab a coffee. ☕</li>
</ol>
</td>
</tr>
</table>

We're not just forwarding requests. We're building **deterministic cache keys** from MD5 hashes of `method + URL + headers + body`, so identical business requests always hit the same cache entry—even across different workflow runs.

---

## 🚀 Get Started in 60 Seconds

<div align="center">

| Platform | One-liner |
|:--------:|:----------|
| 🐳 **Docker** | `docker run -p 8000:8000 ghcr.io/yigitkonur/fastapi-proxy` |
| 🐍 **Python** | `pip install -r requirements.txt && uvicorn main:app` |
| ☁️ **Railway/Render** | Deploy from GitHub, set `REDIS_URL` env var |

</div>

### Quick Install (Python)

```bash
# Clone and enter
git clone https://github.com/yigitkonur/fastapi-http-proxy-with-caching.git
cd fastapi-http-proxy-with-caching

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run (works immediately, even without Redis!)
uvicorn main:app --host 0.0.0.0 --port 8000
```

> **✨ Zero Config:** The proxy starts in **degraded mode** without Redis—requests still work, just without caching. Add Redis when you're ready for the full experience.

---

## 🎮 Usage: Fire and Forget

### Basic Proxy Request

```bash
# Instead of calling the API directly...
curl -X POST "https://expensive-api.com/data" -d '{"query": "foo"}'

# Route through the proxy:
curl -X POST "http://localhost:8000/proxy?url=https://expensive-api.com/data" \
  -H "Content-Type: application/json" \
  -d '{"query": "foo"}'
```

### Response Format

```json
{
  "success": true,
  "cached": true,
  "cache_key": "a1b2c3d4e5f67890",
  "status_code": 200,
  "data": { "your": "api response" }
}
```

The `cached: true` means you just saved an API call. 🎉

### In n8n

1. Add an **HTTP Request** node
2. Set URL to: `http://your-proxy:8000/proxy?url=https://actual-api.com/endpoint`
3. Configure method, headers, body as normal
4. Every identical request now returns from cache

### Advanced Options

```bash
# Force fresh request (bypass cache)
curl "http://localhost:8000/proxy?url=https://api.com/data&bypass_cache=true"

# Custom cache TTL (2 hours instead of default 1 hour)
curl "http://localhost:8000/proxy?url=https://api.com/data&cache_ttl=7200"
```

### Health & Admin Endpoints

```bash
# Health check (great for load balancers)
curl http://localhost:8000/health
# → {"status": "healthy", "redis_connected": true, "version": "2.0.0"}

# Cache statistics
curl http://localhost:8000/cache/stats
# → {"total_keys": 1547, "memory_usage": "2.3M", "prefix": "proxy:cache:"}

# Nuclear option: clear all cache
curl -X DELETE http://localhost:8000/cache
# → {"deleted": 1547, "message": "Cleared 1547 cached entries"}
```

---

## ✨ Feature Breakdown: The Secret Sauce

<div align="center">

| Feature | What It Does | Why You Care |
| :---: | :--- | :--- |
| **🧠 MD5 Hashing**<br/>Deterministic keys | Hashes `method + URL + headers + body` into cache key | Identical requests always return same cached response |
| **⚡ Graceful Degradation**<br/>No Redis? No problem | Starts without Redis, just skips caching | Deploy anywhere, add Redis later |
| **🔄 All HTTP Methods**<br/>Not just POST | GET, POST, PUT, DELETE, PATCH all supported | Works with any API pattern |
| **⏰ Flexible TTL**<br/>Per-request control | Default 1 hour, override per request | Cache static data longer, dynamic shorter |
| **🎯 Cache Bypass**<br/>When you need fresh | `bypass_cache=true` skips cache | Force refresh when needed |
| **📊 Health Checks**<br/>Production ready | `/health` endpoint with Redis status | Perfect for k8s liveness probes |
| **🔧 Legacy Support**<br/>Drop-in replacement | `/webhook-test/post-response` still works | Migrate existing workflows gradually |

</div>

---

## ⚙️ Configuration

All settings via environment variables. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

<div align="center">

| Variable | Default | Description |
|:---------|:--------|:------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection (or Upstash URL) |
| `CACHE_TTL_SECONDS` | `3600` | Default cache lifetime (1 hour) |
| `CACHE_PREFIX` | `proxy:cache:` | Redis key prefix |
| `PROXY_TIMEOUT_SECONDS` | `30` | Timeout for proxied requests |
| `DEBUG` | `false` | Enable verbose logging |

</div>

### Using Upstash (Serverless Redis)

[Upstash](https://upstash.com/) is perfect for this—pay only for what you use:

1. Create a database at [console.upstash.com](https://console.upstash.com)
2. Copy your Redis URL
3. Set in `.env`:
   ```
   REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379
   ```

**Cost**: ~$0.20 per 100K cached requests. If you're making 1M duplicate calls/month, that's **$2 vs whatever you're paying now**.

---

## 🏗️ Project Structure

```
├── main.py                 # Entry point (thin wrapper)
├── app/
│   ├── __init__.py        # Package metadata
│   ├── main.py            # FastAPI app factory + lifespan
│   ├── config.py          # Pydantic settings from env
│   ├── models.py          # Request/response schemas
│   ├── dependencies.py    # Service injection
│   ├── services/
│   │   ├── cache.py       # Redis + MD5 hashing logic
│   │   └── proxy.py       # HTTP forwarding logic
│   └── routes/
│       ├── proxy.py       # /proxy endpoint
│       └── health.py      # /health, /cache/stats
├── requirements.txt       # Pinned dependencies
├── Dockerfile            # Multi-stage production build
├── .env.example          # Configuration template
└── README.md
```

---

## 🐳 Deployment

### Docker (Recommended)

```bash
# Build
docker build -t fastapi-proxy .

# Run (without Redis - degraded mode)
docker run -p 8000:8000 fastapi-proxy

# Run with Redis
docker run -p 8000:8000 -e REDIS_URL=redis://host:6379 fastapi-proxy
```

### Docker Compose (with Redis)

```yaml
version: '3.8'
services:
  proxy:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
volumes:
  redis_data:
```

### Systemd (Linux Server)

```ini
[Unit]
Description=FastAPI Transparent Proxy
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/fastapi-proxy
Environment="PATH=/opt/fastapi-proxy/venv/bin"
ExecStart=/opt/fastapi-proxy/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 🔥 Common Issues & Quick Fixes

<details>
<summary><b>Expand for troubleshooting tips</b></summary>

| Problem | Solution |
| :--- | :--- |
| **"Redis unavailable" warning** | Expected without Redis. The proxy still works, just without caching. Add `REDIS_URL` when ready. |
| **Cache not working** | Check `redis_connected: true` in `/health`. Verify your `REDIS_URL` is correct. |
| **Timeout errors** | Increase `PROXY_TIMEOUT_SECONDS`. Some APIs are slow. |
| **Cache key collisions** | Shouldn't happen—MD5 is deterministic. If you're seeing wrong cached responses, check if you're modifying headers unintentionally. |
| **High memory usage** | Set `CACHE_TTL_SECONDS` lower, or use `/cache` DELETE endpoint to clear. |

</details>

---

## 🛠️ Development

```bash
# Clone
git clone https://github.com/yigitkonur/fastapi-http-proxy-with-caching.git
cd fastapi-http-proxy-with-caching

# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --reload

# Run tests (coming soon)
pytest
```

---

<div align="center">

**Built with 🔥 because paying for duplicate API calls is a soul-crushing waste of money.**

MIT © [Yiğit Konur](https://github.com/yigitkonur)

</div>
