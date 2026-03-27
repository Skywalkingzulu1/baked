# Bud Credit Form Application

## Table of Contents
- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Docker Build & Run](#docker-build--run)
- [Nginx Configuration](#nginx-configuration)
- [Deployment Workflow](#deployment-workflow)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Project Overview
The **Bud Credit Form** is a simple web application that allows users to submit credit‑related information. It consists of:

- A static HTML front‑end (`index.html`) styled with Bootstrap.
- A Flask back‑end (`app.py`) that serves the static files and provides a health‑check endpoint.
- A `requirements.txt` file that lists Python dependencies.

The application is containerised for easy deployment and can be served behind an Nginx reverse proxy.

---

## Architecture
```
┌─────────────────────┐
│   Client Browser    │
│ (HTML + JS)         │
└─────────▲───────────┘
          │ HTTP(S)
┌─────────▼───────────┐
│      Nginx          │  ←  Reverse proxy, SSL termination, static caching
│ (optional)          │
└─────────▲───────────┘
          │ HTTP
┌─────────▼───────────┐
│   Flask (app.py)    │  ←  Serves index.html & health endpoint
│   (Gunicorn/WSGI)   │
└─────────────────────┘
```

- **Front‑end**: `index.html` (static assets, Bootstrap, Web3 integration).
- **Back‑end**: `app.py` (Flask) – serves static files from the `static` folder and exposes `/health`.
- **Containerisation**: Dockerfile builds a lightweight Python image.
- **Reverse Proxy**: Nginx can be used to expose the container on port 80/443 and handle SSL.

---

## Prerequisites
- **Python 3.11+** (for local development)
- **Docker** (for containerised builds)
- **Docker Compose** (optional, if you want to orchestrate Nginx + app)
- **Git** (to clone the repository)

---

## Local Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/bud-credit-form.git
   cd bud-credit-form
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask app**
   ```bash
   python app.py
   ```

5. **Visit the app**
   Open your browser and navigate to `http://localhost:5000`.

---

## Docker Build & Run
A minimal Dockerfile is provided (create `Dockerfile` if not present).

### Dockerfile (example)
```dockerfile
# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Flask default port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
```

### Build the image
```bash
docker build -t bud-credit-form:latest .
```

### Run the container
```bash
docker run -d -p 5000:5000 --name bud-credit-form bud-credit-form:latest
```

The app will be reachable at `http://localhost:5000`.

---

## Nginx Configuration
Below is a sample Nginx configuration (`nginx.conf`) to proxy requests to the Flask container and serve static assets efficiently.

```nginx
# /etc/nginx/conf.d/bud_credit.conf
server {
    listen 80;
    server_name your-domain.com;

    # Optional: enable HTTP -> HTTPS redirect
    # return 301 https://$host$request_uri;

    # Serve static files directly (if you mount the static folder)
    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://app:5000/health;
    }

    # Optional: enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml+rss;
}
```

### Docker‑Compose (optional)
```yaml
version: "3.8"
services:
  app:
    build: .
    container_name: bud_credit_app
    restart: unless-stopped

  nginx:
    image: nginx:stable-alpine
    container_name: bud_credit_nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - app
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

---

## Deployment Workflow
1. **Commit & Push** – Ensure all changes are pushed to the main branch.
2. **CI/CD Pipeline** – (e.g., GitHub Actions, GitLab CI) should:
   - Lint and run tests.
   - Build the Docker image and push to a container registry (Docker Hub, GitHub Packages, etc.).
   - Deploy the image to the target environment (Kubernetes, ECS, Azure Web Apps, etc.).
3. **Infrastructure** – Provision an instance or managed service that runs the Docker container behind Nginx.
4. **SSL** – Use Let’s Encrypt (certbot) or a cloud provider’s managed certificates.
5. **Monitoring** – Health endpoint (`/health`) can be scraped by Prometheus or used by load balancers.

*Tip:* Keep environment‑specific values (e.g., contract address, API keys) in a `.env` file and load them with `python-dotenv`. Do **not** commit secrets.

---

## Testing
The project includes `pytest` and `pytest-asyncio` for unit and async tests.

```bash
pytest
```

Add your test modules under a `tests/` directory. Example test skeleton:

```python
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

---

## Contributing
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome-feature`).
3. Commit your changes with clear messages.
4. Open a Pull Request targeting `main`.
5. Ensure CI passes before merging.

Please adhere to the existing code style and include documentation updates when adding new functionality.

---

## License
This project is licensed under the **MIT License** – see the `LICENSE` file for details.