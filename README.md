# PrioPick API

Smart budget planner API that uses AI to suggest
the best combination of vendors within your budget.

## Tech Stack
- **FastAPI** — Python web framework
- **PostgreSQL** — Database
- **Redis** — Caching
- **Ollama + Llama3.2** — Local AI (free)
- **Docker** — Containerization
- **SQLAlchemy 2.0** — Async ORM

## Architecture
Modular monolith with clean layered architecture:
Router → Service → Repository → Database

## Modules
- **Auth** — JWT authentication
- **Vendors** — Vendor marketplace with filtering
- **Plans** — AI-powered budget planning

## Run Locally
```bash
# Start AI
ollama serve

# Start everything
docker compose up --build

# Open docs
http://localhost:8000/docs
```
