# loan-api

FastAPI service that scores loan applications with a scikit-learn model and
returns the probability of default, a risk band and a decision.

## Files

| File | Purpose |
|------|---------|
| `main.py` | The API. Reads the model from `MODEL_PATH`; saves predictions to Postgres when `DATABASE_URL` is set. |
| `train.py` | Trains the model on synthetic data and writes `model/loan_model.joblib`. |
| `Dockerfile` | Development image (dev tools, auto reload). |
| `Dockerfile.prod` | Production image: multi-stage, pinned slim base, non-root user, health check. |
| `.dockerignore` | Keeps `.git`, venvs, `.env`, tests and docs out of the build context. |
| `compose.yaml` | Runs the API (built from `Dockerfile.prod`) with Postgres. |
| `init.sql` | Creates the `predictions` table on the first database start. |
| `requirements.txt` / `requirements-dev.txt` | Runtime and development dependencies (pinned). |
| `CHECKLIST.md` | Evidence for each production requirement. |

## Run

```bash
# With Compose (API + Postgres)
docker compose up -d --build
# open http://localhost:8000/docs

# If port 8000 is busy on your machine
API_PORT=8010 docker compose up -d --build

# From Docker Hub, no local files needed
docker run --rm -p 8000:8000 <dockerhub-username>/loan-api:1.0.0
```

Example request:

```bash
curl -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"income":1200,"loan_amount":5000,"term_months":24,"credit_score":680,"employment_years":4}'
```

## Development

```bash
pip install -r requirements-dev.txt
python train.py      # rebuild the model
pytest -q            # run tests
ruff check .         # lint
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_PATH` | `/app/model/loan_model.joblib` | Path to the trained model file. |
| `DATABASE_URL` | not set | Postgres URL. When unset, predictions are not stored. |
| `LOG_LEVEL` | `INFO` | Python log level. |
