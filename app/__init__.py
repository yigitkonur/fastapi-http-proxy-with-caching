"""
FastAPI Transparent HTTP Proxy with Caching

A no-code friendly transparent HTTP proxy that caches responses based on
MD5 hash of request signatures. Ideal for:
- No-code/low-code platforms (n8n, Make, Zapier) that need response caching
- Reducing duplicate API calls to expensive third-party services
- Development environments where you need deterministic responses

The proxy generates an MD5 hash of the request (URL + headers + body) and
returns cached responses for identical requests, saving bandwidth and API costs.
"""

__version__ = "2.0.0"
__author__ = "Yigit Konur"
