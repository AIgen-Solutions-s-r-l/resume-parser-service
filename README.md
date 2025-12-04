<div align="center">

# 🚀 Resume Parser Service

**Transform PDF resumes into structured data at scale.**

[![CI](https://img.shields.io/github/actions/workflow/status/AIgen-Solutions-s-r-l/resume-parser-service/ci.yml?branch=main&style=for-the-badge&logo=github&label=CI)](https://github.com/AIgen-Solutions-s-r-l/resume-parser-service/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen?style=for-the-badge&logo=pytest)](https://github.com/AIgen-Solutions-s-r-l/resume-parser-service)
[![Python](https://img.shields.io/badge/python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://hub.docker.com)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000?style=for-the-badge)](https://github.com/psf/black)

</div>

---

## 💡 Mission

> **We eliminate the friction between PDF resumes and structured data.**
> Powered by AI, built for scale.

---

## 🛠 Tech Stack

<table>
<tr>
<td align="center" width="96">
<img src="https://skillicons.dev/icons?i=fastapi" width="48" height="48" alt="FastAPI" />
<br>FastAPI
</td>
<td align="center" width="96">
<img src="https://skillicons.dev/icons?i=python" width="48" height="48" alt="Python" />
<br>Python 3.12
</td>
<td align="center" width="96">
<img src="https://skillicons.dev/icons?i=mongodb" width="48" height="48" alt="MongoDB" />
<br>MongoDB
</td>
<td align="center" width="96">
<img src="https://skillicons.dev/icons?i=docker" width="48" height="48" alt="Docker" />
<br>Docker
</td>
<td align="center" width="96">
<img src="https://skillicons.dev/icons?i=azure" width="48" height="48" alt="Azure" />
<br>Azure AI
</td>
<td align="center" width="96">
<img src="https://skillicons.dev/icons?i=kubernetes" width="48" height="48" alt="K8s" />
<br>Kubernetes
</td>
</tr>
<tr>
<td align="center" width="96">
<img src="https://cdn.simpleicons.org/openai/412991" width="48" height="48" alt="OpenAI" />
<br>GPT-4o
</td>
<td align="center" width="96">
<img src="https://skillicons.dev/icons?i=redis" width="48" height="48" alt="Cache" />
<br>TTL Cache
</td>
<td align="center" width="96">
<img src="https://skillicons.dev/icons?i=githubactions" width="48" height="48" alt="CI/CD" />
<br>GitHub Actions
</td>
<td align="center" width="96">
<img src="https://cdn.simpleicons.org/pydantic/E92063" width="48" height="48" alt="Pydantic" />
<br>Pydantic
</td>
<td align="center" width="96">
<img src="https://cdn.simpleicons.org/pytest/0A9EDC" width="48" height="48" alt="Pytest" />
<br>Pytest
</td>
<td align="center" width="96">
<img src="https://cdn.simpleicons.org/jsonwebtokens/000000" width="48" height="48" alt="JWT" />
<br>JWT Auth
</td>
</tr>
</table>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔮 **Dual OCR Strategy** | Azure Document Intelligence + GPT-4o Vision for maximum accuracy |
| ⚡ **Async-First** | Non-blocking I/O with proper async patterns throughout |
| 🔐 **Secure by Default** | JWT auth, input validation, security headers |
| 📦 **Production-Ready** | Docker, K8s health probes, structured logging |
| 🚀 **High Performance** | In-memory caching, GZip compression, database indexes |
| 🧪 **Well-Tested** | Unit tests, integration tests with testcontainers |

---

## 🏗 Architecture

```mermaid
flowchart TB
    subgraph Client["👤 Client"]
        A[Web App / Mobile]
    end

    subgraph Gateway["🌐 API Gateway"]
        B[FastAPI]
        B1[JWT Auth]
        B2[Rate Limiting]
        B3[CORS]
    end

    subgraph Services["⚙️ Services"]
        C[Resume Parser]
        D[Resume Service]
        E[Health Check]
    end

    subgraph AI["🤖 AI Layer"]
        F[Azure Document Intelligence]
        G[OpenAI GPT-4o Vision]
    end

    subgraph Data["💾 Data Layer"]
        H[(MongoDB)]
        I[TTL Cache]
    end

    A -->|HTTPS| B
    B --> B1 --> B2 --> B3
    B3 --> C & D & E
    C --> F & G
    C --> D
    D --> H
    D --> I
    E --> H

    style Client fill:#1a1a2e,stroke:#00d4ff,color:#fff
    style Gateway fill:#16213e,stroke:#00d4ff,color:#fff
    style Services fill:#0f3460,stroke:#e94560,color:#fff
    style AI fill:#1a1a2e,stroke:#00ff88,color:#fff
    style Data fill:#16213e,stroke:#ffd700,color:#fff
```

---

## 🔄 PDF Processing Pipeline

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant V as Validator
    participant Azure as Azure OCR
    participant GPT as GPT-4o Vision
    participant LLM as LLM Combiner
    participant DB as MongoDB

    C->>+API: POST /resumes/pdf_to_json
    API->>+V: Validate PDF (size, format, structure)
    V-->>-API: Valid ✓

    par Parallel OCR
        API->>+Azure: Extract text
        Azure-->>-API: OCR Result
    and
        API->>+GPT: Vision analysis
        GPT-->>-API: Structured data
    end

    API->>+LLM: Combine & merge results
    LLM-->>-API: Final JSON

    API->>API: Repair & validate JSON
    API-->>-C: 200 OK + Resume JSON

    Note over API,DB: Optional: Save to database
```

---

## 🚀 Deployment View

```mermaid
C4Deployment
    title Deployment Diagram

    Deployment_Node(cloud, "Cloud Platform", "AWS / Azure / GCP") {
        Deployment_Node(k8s, "Kubernetes Cluster") {
            Deployment_Node(ns, "resume-parser namespace") {
                Container(api, "API Pods", "FastAPI", "Handles HTTP requests")
                Container(worker, "Worker Pods", "Celery", "Background tasks")
            }
        }

        Deployment_Node(managed, "Managed Services") {
            ContainerDb(mongo, "MongoDB Atlas", "Document Store")
            Container(azure, "Azure AI", "Document Intelligence")
            Container(openai, "OpenAI API", "GPT-4o Vision")
        }
    }

    Rel(api, mongo, "reads/writes", "TLS")
    Rel(api, azure, "OCR requests", "HTTPS")
    Rel(api, openai, "Vision requests", "HTTPS")
```

---

## 🔧 Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- MongoDB 7.0+
- Azure & OpenAI API keys

### Quick Start

```bash
# Clone
git clone https://github.com/AIgen-Solutions-s-r-l/resume-parser-service.git
cd resume-parser-service

# Configure
cp .env.example .env
# Edit .env with your API keys

# Launch
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

### Local Development

```bash
# Install dependencies
pip install poetry && poetry install

# Run with hot reload
uvicorn app.main:app --reload

# Run tests
pytest --cov=app
```

---

## 📡 API Overview

### Endpoints

| Method | Endpoint | Description |
|:------:|----------|-------------|
| `POST` | `/resumes/pdf_to_json` | Convert PDF → JSON |
| `POST` | `/resumes/create_resume` | Create resume |
| `GET` | `/resumes/get` | Get user's resume |
| `PUT` | `/resumes/update` | Update resume |
| `GET` | `/resumes/exists` | Check existence |

### Health & Metrics

| Method | Endpoint | Purpose |
|:------:|----------|---------|
| `GET` | `/health` | Service health |
| `GET` | `/ready` | K8s readiness |
| `GET` | `/live` | K8s liveness |
| `GET` | `/metrics/cache` | Cache stats |

### Example Request

```bash
curl -X POST "http://localhost:8000/resumes/pdf_to_json" \
  -H "Authorization: Bearer $TOKEN" \
  -F "pdf_file=@resume.pdf"
```

---

## ⚙️ Configuration

| Variable | Description | Required |
|----------|-------------|:--------:|
| `MONGODB` | Connection string | ✅ |
| `SECRET_KEY` | JWT secret (32+ chars) | ✅ |
| `OPENAI_API_KEY` | OpenAI API key | ✅ |
| `DOCUMENT_INTELLIGENCE_API_KEY` | Azure key | ✅ |
| `DOCUMENT_INTELLIGENCE_ENDPOINT` | Azure endpoint | ✅ |
| `LOG_LEVEL` | DEBUG/INFO/WARNING/ERROR | |
| `ENVIRONMENT` | development/production | |

---

## 🗺 Roadmap

```mermaid
gantt
    title Product Roadmap
    dateFormat  YYYY-MM-DD
    section Core
    PDF Parsing          :done, 2024-01-01, 30d
    Multi-OCR Strategy   :done, 2024-01-15, 20d
    Caching Layer        :done, 2024-02-01, 10d

    section Scale
    Redis Cache          :active, 2024-03-01, 15d
    Async Queue          :2024-03-15, 20d
    Multi-tenant         :2024-04-01, 30d

    section AI
    Resume Scoring       :2024-04-15, 25d
    Skill Extraction     :2024-05-01, 20d
    Job Matching         :2024-05-15, 30d
```

| Priority | Feature | Status |
|:--------:|---------|:------:|
| **P1** | Redis distributed cache | 🔄 In Progress |
| **P1** | Async job queue (Celery) | 📋 Planned |
| **P2** | Multi-tenant support | 📋 Planned |
| **P2** | Resume quality scoring | 📋 Planned |
| **P3** | AI-powered skill extraction | 💡 Ideation |
| **P3** | Job-resume matching | 💡 Ideation |

---

## 🤝 Contributing

We love contributions! Here's how to get started:

```bash
# Fork & clone
git clone https://github.com/YOUR_USERNAME/resume-parser-service.git

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes & test
pytest && pre-commit run --all-files

# Commit with conventional commits
git commit -m "feat: add amazing feature"

# Push & create PR
git push origin feature/amazing-feature
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

```
MIT License

Copyright (c) 2024 AIgen Solutions s.r.l.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software.
```

---

<div align="center">

**Built with ❤️ by [AIgen Solutions](https://github.com/AIgen-Solutions-s-r-l)**

[Report Bug](https://github.com/AIgen-Solutions-s-r-l/resume-parser-service/issues) · [Request Feature](https://github.com/AIgen-Solutions-s-r-l/resume-parser-service/issues) · [Documentation](https://github.com/AIgen-Solutions-s-r-l/resume-parser-service/wiki)

</div>
