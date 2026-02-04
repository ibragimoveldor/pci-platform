# PCI Platform

A scalable Pavement Condition Index (PCI) analysis platform built with FastAPI, React, Celery, and PostgreSQL.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer                           │
└─────────────────────────────────────────────────────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
    ┌──────────┐          ┌──────────┐          ┌──────────┐
    │ FastAPI  │          │ FastAPI  │          │ FastAPI  │
    └──────────┘          └──────────┘          └──────────┘
                                │
    ┌───────────────────────────┼───────────────────────────┐
    ▼                           ▼                           ▼
┌──────────┐              ┌──────────┐              ┌──────────┐
│PostgreSQL│              │  Redis   │              │  MinIO   │
└──────────┘              └──────────┘              └──────────┘
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        ┌──────────┐      ┌──────────┐      ┌──────────┐
        │  Celery  │      │  Celery  │      │  Celery  │
        │  Worker  │      │  Worker  │      │  Worker  │
        └──────────┘      └──────────┘      └──────────┘
```

## Features

- **JWT Authentication** with refresh tokens
- **Project Management** - CRUD operations
- **Image Upload** - Drag & drop to S3-compatible storage
- **Async ML Processing** - Background tasks with Celery
- **Real-time Progress** - Live status updates
- **PCI Calculation** - Automated scoring
- **Horizontal Scaling** - Scale API and workers independently

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Frontend | React 18, TypeScript, TailwindCSS |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Storage | MinIO (S3-compatible) |
| Tasks | Celery |

## Quick Start

```bash
# Start all services
docker compose up -d

# Access
# - Frontend: http://localhost:3000
# - API Docs: http://localhost:8000/docs
# - MinIO: http://localhost:9001

# Create test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## Project Structure

```
pci-platform/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Settings
│   │   ├── api/v1/           # API routes
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── core/             # Database, Redis, Storage
│   │   ├── workers/          # Celery tasks
│   │   └── ml/               # ML models (placeholder)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/              # API client
│       ├── pages/            # React pages
│       └── components/       # UI components
└── nginx/
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create project |
| POST | `/api/v1/projects/{id}/images` | Upload images |
| POST | `/api/v1/projects/{id}/analysis/start` | Start analysis |
| GET | `/api/v1/projects/{id}/analysis/status` | Check status |

## Integrating Your ML Models

Replace the placeholder in `backend/app/ml/__init__.py`:

```python
from ultralytics import YOLO

class YOLODetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
    
    def detect(self, image):
        return self.model.predict(image)
```

## Scaling

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      replicas: 3
  celery-worker:
    deploy:
      replicas: 5
```

## Environment Variables

| Variable | Default |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://pci:pci_secret@postgres:5432/pci_db` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `MINIO_ENDPOINT` | `minio:9000` |
| `SECRET_KEY` | `change-in-production` |

## License

MIT
