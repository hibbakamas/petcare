


# PetCare

A **household pet management web application** built with **Flask** and **PostgreSQL**, improved using **DevOps practices**, such as automated testing, CI/CD pipelines, containerization, and cloud deployment on **Azure**.

Users can create or join households, add pets, and record notes for each pet, now supported by a full production pipeline and monitoring setup.

---

## Live Deployment

**Azure Web App URL:**
[https://petcare-web.azurewebsites.net](https://petcare-web.azurewebsites.net)

---

## Features

* Create or join a household with a unique join code
* Add, edit, and delete pets
* Log entries for each pet (feeding, vet visits, etc.)
* View and manage household members
* Login, signup, and profile management
* REST API and UI routes
* Automated tests (91% coverage)
* CI/CD pipeline with GitHub Actions
* Deployed to Azure Web App via Docker and Service Principal
* Real-time health check (`/health`) and Prometheus metrics (`/metrics`)

---

## Project Overview

| Category           | Technology                              |
| ------------------ | --------------------------------------- |
| **Framework**      | Flask (Python 3.12)                     |
| **Database**       | PostgreSQL Flexible Server (Azure)      |
| **ORM**            | SQLAlchemy + Flask-Migrate              |
| **Testing**        | Pytest + Pytest-Cov                     |
| **CI/CD**          | GitHub Actions + Docker + Azure Web App |
| **Monitoring**     | Prometheus metrics, `/health` endpoint  |
| **Container**      | Docker image hosted on Docker Hub       |
| **Cloud Provider** | Microsoft Azure                         |

---

## Local Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/hibbakamas/petcare.git
cd petcare
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

For development & tests:

```bash
pip install -r requirements-dev.txt
```

---

## Running Tests

To verify functionality and coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

All tests use an **in-memory SQLite database**, ensuring isolation and reproducibility.

---

## Running with Docker

### Build the image

```bash
docker build -t petcare .
```

### Run locally

```bash
docker run -p 5000:5000 petcare
```

Then visit **[http://localhost:5000](http://localhost:5000)**

---

## Deployment (CI/CD)

### GitHub Actions

Every push to `main` triggers the workflow defined in `.github/workflows/ci-cd.yml`.

**Pipeline stages:**

1. Run tests and enforce coverage ≥70%.
2. Build and push Docker image to Docker Hub.
3. Deploy automatically to Azure Web App using a Service Principal (`AZURE_CREDENTIALS`).

Secrets used:

* `DOCKERHUB_USERNAME`
* `DOCKERHUB_TOKEN`
* `AZURE_CREDENTIALS`

---

## Monitoring and Health Checks

### `/health`

Simple status endpoint confirming app and DB connectivity.

```json
{"status": "ok"}
```

### `/metrics`

Exposes Prometheus-formatted metrics for:

* Total request count
* Request latency
* Server error rates

Example metrics:

```
# HELP petcare_request_total Total HTTP requests
# TYPE petcare_request_total counter
petcare_request_total{method="GET",endpoint="login"} 5.0
```

### Prometheus configuration

`monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: "petcare"
    metrics_path: /metrics
    static_configs:
      - targets:
          - "host.docker.internal:5000"
        labels:
          service: "petcare"
          env: "dev"
```

To run locally:

```bash
docker run -p 9090:9090 -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
```

Then open [http://localhost:9090](http://localhost:9090) → see “petcare — UP”.

---

## Project Structure

```
app/
 ├── app.py                 # Main entrypoint
 ├── __init__.py            # App factory (create_app)
 ├── models.py              # SQLAlchemy models
 ├── db.py                  # DB setup (SQLite/Postgres)
 ├── config.py              # Configuration classes
 ├── routes/                # API + UI blueprints
 ├── templates/             # Jinja2 HTML templates
 ├── static/                # CSS, JS assets
 ├── utils/                 # Helpers and formatters
monitoring/
 ├── prometheus.yml         # Local Prometheus config
tests/                      # Unit and integration tests
.github/workflows/ci-cd.yml    # CI/CD pipeline
Dockerfile
requirements.txt
requirements-dev.txt
README.md
```

---

## Improvements Implemented

| Category             | Improvements                                                |
| -------------------- | ----------------------------------------------------------- |
| **Code Quality**     | Refactored code using SOLID principles, removed code smells |
| **Testing**          | Achieved 91% coverage using `pytest` and `pytest-cov`       |
| **CI/CD**            | Automated testing, Docker build, and Azure deployment       |
| **Containerization** | Created lightweight production image (Python 3.12-slim)     |
| **Deployment**       | Fully automated GitHub → Azure pipeline                     |
| **Monitoring**       | `/health` and `/metrics` endpoints + Prometheus config      |
| **Database**         | Migrated from SQLite to persistent Azure PostgreSQL         |

---

## Credits

Developed by **Hibba Kamas**  
Bachelor in Computer Science & Artificial Intelligence  
IE University, Fall 2025
