import json
import hashlib
import httpx
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis configuration
# Replace with your Redis URL
redis_url = "your_redis_url_here"
redis_client = aioredis.from_url(redis_url, decode_responses=True)

async def generate_cache_key(url: str, headers: dict, body: bytes) -> str:
    """Generate a unique cache key based on the URL, headers, and body."""
    combined_data = {
        "url": url,
        "headers": {k: v for k, v in sorted(headers.items())},
        "body": body.decode('utf-8')
    }
    json_data = json.dumps(combined_data, sort_keys=True)
    return hashlib.sha256(json_data.encode('utf-8')).hexdigest()

@app.post("/webhook-test/post-response")
async def proxy_request(request: Request):
    """Proxy the incoming request to the specified URL and handle caching."""
    # Step 1: Extract Incoming Request Data
    url = request.query_params.get("url")
    if not url:
        logger.error("Missing 'url' query parameter")
        raise HTTPException(status_code=400, detail="Missing 'url' query parameter")
    
    headers = dict(request.headers)
    body = await request.body()
    
    logger.info(f"Received request for URL: {url}")
    
    # Step 2: Generate Cache Key
    cache_key = await generate_cache_key(url, headers, body)
    logger.info(f"Generated cache key: {cache_key}")
    
    # Step 3: Check Cache
    cached_response = await redis_client.get(cache_key)
    if cached_response:
        logger.info("Cache hit, returning cached response")
        return JSONResponse(status_code=200, content=json.loads(cached_response))
    
    logger.info("Cache miss, forwarding request to target URL")
    
    # Step 4: Forward the Request
    # Remove headers that could cause issues
    headers_to_exclude = ["host", "content-length", "connection", "accept-encoding"]
    filtered_headers = {k: v for k, v in headers.items() if k.lower() not in headers_to_exclude}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=filtered_headers, content=body)
            response.raise_for_status()
            logger.info(f"Received response from target URL with status: {response.status_code}")
    except httpx.RequestError as exc:
        logger.error(f"Request error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP status error: {exc.response.text}")
        return JSONResponse(status_code=exc.response.status_code, content={"error": exc.response.text})
    
    # Step 5: Cache and Return Response
    response_content = response.json()
    await redis_client.set(cache_key, json.dumps(response_content))
    logger.info("Response cached successfully")
    
    return JSONResponse(status_code=response.status_code, content=response_content)

# To run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
