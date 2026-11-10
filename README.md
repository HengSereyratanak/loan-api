# loan-api

Loan Application Service: stores loan applications and scores their default risk.
Endpoints: `GET /health`, `POST /api/v1/predictions`, `/api/v1/applications`.

## Files

| File | Purpose |
|------|---------|
| `main.py`, `schemas.py` | FastAPI app; model path from `MODEL_PATH` |
| `train.py` | Trains the model (`--version`, `--out`) |
| `Dockerfile` | Single-stage image (Lesson 4.3) |
| `Dockerfile.prod` | Multi-stage production image: slim, `appuser`, `HEALTHCHECK` |
| `.dockerignore` | Excludes Git, caches, local models and dev config |
| `compose.yaml` | API + PostgreSQL + Adminer |
| `init.sql` | Seed data for PostgreSQL |
| `requirements.txt` / `requirements-dev.txt` | Production / development packages |
| `CHECKLIST.md` | Evidence for each requirement |

## Run

```bash
docker compose up -d --build          # API on :8000, Adminer on :8080
docker run --rm -p 8000:8000 meghoing/loan-api:1.0.0
```

## Develop

```bash
pip install -r requirements-dev.txt
python train.py
pytest -v
```
