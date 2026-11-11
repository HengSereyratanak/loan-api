# loan-api

Loan Application Service: stores loan applications and scores their default risk.

- Live app: https://loan-api-sereyratanak.onrender.com ([/docs](https://loan-api-sereyratanak.onrender.com/docs), [/health](https://loan-api-sereyratanak.onrender.com/health))
- Release branch for the Module 6 capstone: `capstone` (main keeps the Module 4 submission)

## Endpoints

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | Status, model version and the deployed commit (`git_sha`) |
| POST | `/api/v1/predictions` | Default probability and risk band |
| GET, POST | `/api/v1/applications` | List and create applications |
| GET | `/api/v1/applications/{id}` | One application |
| PATCH | `/api/v1/applications/{id}` | Approve or reject; a decision is final (409) |

In production every `/api/` route needs an `X-API-Key` header (`API_KEY` is set on Render).

## Pipeline

`.github/workflows/pipeline.yml`: pull requests run `test`; merges to `capstone` run
test -> build-and-push (ghcr.io, tagged with the commit SHA) -> deploy (Render deploy hook) -> verify (`/health` reports the SHA).

## Files

| File | Purpose |
|------|---------|
| `main.py`, `schemas.py` | FastAPI app; model from the MLflow registry or `MODEL_PATH` |
| `train.py` | Trains the model file (`--version`, `--out`) |
| `Dockerfile.prod` | Multi-stage production image: slim, `appuser`, `HEALTHCHECK`, `GIT_SHA` |
| `Dockerfile`, `compose.yaml`, `init.sql` | Module 4: single-stage image, API + PostgreSQL + Adminer |
| `train_tracked.py`, `register.py`, `set_champion.py` | Module 5: tracked runs, registry, champion alias |
| `monitor.py`, `drift_chart.py`, `psi.py`, `data.py`, `compare_runs.py` | Module 5: drift monitoring and charts |
| `CHECKLIST.md` | Module 4 evidence |

## Develop

```bash
pip install -r requirements-dev.txt
python train.py
pytest -v
```
