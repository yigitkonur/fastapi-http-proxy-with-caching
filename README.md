# FastAPI HTTP Proxy with Caching

A FastAPI-based HTTP proxy that forwards requests to specified URLs, while caching responses using Redis to optimize repeated requests. This implementation includes detailed logging to track the flow of requests and caching mechanisms.

## Features

- Forward HTTP POST requests to specified URLs.
- Cache responses to avoid redundant network calls.
- Detailed logging for easy debugging and monitoring.
- Configurable with Redis for caching.

## Getting Started

### Prerequisites

- Python 3.7+
- FastAPI
- Redis (Upstash or local Redis instance)
- httpx
- uvicorn

### Installation

1. Clone the repository:

```sh
git clone https://github.com/yourusername/fastapi-http-proxy-with-caching.git
cd fastapi-http-proxy-with-caching
```

2. Create a virtual environment and activate it:

```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install the dependencies:

```sh
pip install -r requirements.txt
```

### Configuration

Configure your Redis URL in the `redis_url` variable inside `main.py`. You can use a local Redis instance or a cloud-based service like Upstash.

### Running the Application

Start the FastAPI server using uvicorn:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Usage

Send a POST request to the `/webhook-test/post-response` endpoint with a `url` query parameter specifying the target URL.

Example:

```sh
curl -X POST "http://127.0.0.1:8000/webhook-test/post-response?url=https://example.com/api" -H "Content-Type: application/json" -d '{"key": "value"}'
```

### Logging

The application includes detailed logging to help trace the flow of requests and responses. Logs are printed to the console.
