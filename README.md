# FastAPI HTTP Proxy with Caching

A FastAPI-based HTTP proxy that forwards requests to specified URLs, while caching responses using Redis to optimize repeated requests. This implementation includes detailed logging to track the flow of requests and caching mechanisms.

## Features

- Forward HTTP POST requests to specified URLs.
- Cache responses to avoid redundant network calls.
- Detailed logging for easy debugging and monitoring.
- Configurable with Redis for caching.
- Set up as a systemd service for automatic startup and resource monitoring.

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

### Using Upstash for Redis Caching

#### Introduction to Upstash

[Upstash](https://upstash.com/) is a serverless database solution that offers Redis-compatible caching with a pay-as-you-go pricing model. It is an excellent choice for applications that require scalable and cost-effective caching.

#### Pricing Details

Upstash's pricing model is straightforward and cost-effective, making it a great choice for caching needs:

- **Pay as You Go**: $0.2 per 100K commands
- **Pro 2K**: $280 per month
- **Pro 10K**: $680 per month

For example, caching:
- **1 million objects**: This would typically involve around 1 million commands. At $0.2 per 100K commands, the cost would be $2.
- **10 million requests**: Assuming each request involves a caching command, this would cost $20 at the pay-as-you-go rate.

#### Configuration

To use Upstash as your Redis provider, follow these steps:

1. **Sign Up for Upstash**:
   - Go to [Upstash's website](https://upstash.com/) and sign up for an account.
   - Create a new Redis database and note the provided endpoint and credentials.

2. **Configure Redis URL in the Application**:
   - Open `main.py` and set the `redis_url` variable with your Upstash Redis credentials:

     ```python
     redis_url = "redis://:your_upstash_password@your_upstash_endpoint:your_upstash_port"
     ```

3. **Run the Application**:
   - Start the FastAPI server using uvicorn:

     ```sh
     uvicorn main:app --host 0.0.0.0 --port 8000
     ```

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

### Setting Up as a Systemd Service

To ensure that your FastAPI application runs automatically on system restart and operates as a background service, you can set it up as a systemd service on your server.

#### Finding the Required Paths and Information

1. **Finding the Uvicorn Path:**

    Ensure that the virtual environment is activated:

    ```sh
    source /path/to/your/venv/bin/activate
    ```

    Then find the path to the `uvicorn` executable:

    ```sh
    which uvicorn
    ```

    This will output something like:

    ```sh
    /path/to/your/venv/bin/uvicorn
    ```

    Use this path in the `ExecStart` directive of your systemd service file.

2. **Finding Your Username:**

    Your username can be found by running:

    ```sh
    whoami
    ```

    This will output your current user's name, which should be used in the `User` directive.

3. **Finding the Working Directory:**

    The working directory is where your FastAPI application (e.g., `main.py`) is located. Use the `pwd` command in your project directory to find the full path:

    ```sh
    pwd
    ```

    This will output something like:

    ```sh
    /path/to/your/fastapi-app
    ```

    Use this path in the `WorkingDirectory` directive.

4. **Setting Up the Environment Path:**

    The environment path should point to the `bin` directory of your virtual environment. It is typically:

    ```sh
    /path/to/your/venv/bin
    ```

#### Creating and Configuring the Systemd Service

1. **Create the Systemd Service File:**

    ```sh
    sudo nano /etc/systemd/system/fastapi.service
    ```

2. **Add the Following Content to the Service File:**

    Replace the placeholders with the actual paths and user information found in the steps above.

    ```ini
    [Unit]
    Description=FastAPI Service
    After=network.target

    [Service]
    User=your_username
    Group=www-data
    WorkingDirectory=/path/to/your/fastapi-app
    Environment="PATH=/path/to/your/venv/bin"
    ExecStart=/path/to/your/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

    [Install]
    WantedBy=multi-user.target
    ```

3. **Reload Systemd Daemon:**

    ```sh
    sudo systemctl daemon-reload
    ```

4. **Enable the FastAPI Service to Start on Boot:**

    ```sh
    sudo systemctl enable fastapi.service
    ```

5. **Start the FastAPI Service:**

    ```sh
    sudo systemctl start fastapi.service
    ```

6. **Check the Status of the Service:**

    ```sh
    sudo systemctl status fastapi.service
    ```

### Monitoring System Resources

You can monitor the system resource usage of the FastAPI service using standard Linux tools.

1. **Check CPU and Memory Usage:**

    ```sh
    top
    ```

    Find your service by its name or PID and monitor its resource usage.

2. **Detailed Resource Usage:**

    ```sh
    htop
    ```

    Use `htop` for a more user-friendly and detailed view of system resources.

3. **View Service Logs:**

    ```sh
    sudo journalctl -u fastapi.service -b
    ```

    This command will display detailed logs for the FastAPI service, which can help diagnose any issues.

### Additional Resources

- [Upstash Documentation](https://docs.upstash.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Redis Documentation](https://redis.io/documentation)

By following these steps, you can ensure that your FastAPI application runs correctly as a systemd service and can monitor its resource usage effectively. If there are any further issues, please provide detailed logs for further assistance.
