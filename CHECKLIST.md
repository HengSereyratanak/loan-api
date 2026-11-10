# Production Image Checklist: `loan-api:1.0.0`

Evidence that the production image (`Dockerfile.prod`) meets each requirement.
All commands were run against the image built with:

```bash
docker build -f Dockerfile.prod -t loan-api:1.0.0 .
```

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Small, pinned base image | Done |
| 2 | Multi-stage build, no build or dev tools in the final image | Done |
| 3 | Runs as a non-root user | Done |
| 4 | Health check reports the container as healthy | Done |
| 5 | Configuration from environment variables (`MODEL_PATH`) | Done |
| 6 | No secrets in the image or repository, `.dockerignore` in place | Done |
| 7 | Vulnerability scan with Trivy, HIGH/CRITICAL reviewed | Done (0 CRITICAL, HIGH explained below) |

---

## 1. Small, pinned base image

The base is the `slim` variant, pinned to an exact Python and Debian release (no `latest`).

```console
$ grep -n "^FROM" Dockerfile.prod
4:FROM python:3.12.16-slim-trixie AS builder
18:FROM python:3.12.16-slim-trixie AS runtime
```

## 2. Multi-stage build, no build or dev tools in the final image

Dependencies are installed into `/opt/venv` in the `builder` stage, and only that
venv, `main.py` and the model are copied into the `runtime` stage. pip, pytest and
ruff are not in the production image.

```console
$ docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep -E "loan-api|REPOSITORY"
REPOSITORY:TAG                                      SIZE
loan-api:1.0.0                                      636MB
loan-api:dev                                        691MB

$ docker run --rm --entrypoint sh loan-api:1.0.0 -c "which pip gcc pytest ruff || echo none of pip/gcc/pytest/ruff found"
none of pip/gcc/pytest/ruff found
```

Most of the remaining size is scikit-learn, SciPy and NumPy, which the model needs at runtime.

## 3. Runs as a non-root user

```console
$ docker image inspect loan-api:1.0.0 --format "User: {{.Config.User}}"
User: app

$ docker run --rm loan-api:1.0.0 id
uid=10001(app) gid=10001(app) groups=10001(app)
```

## 4. Health check reports the container as healthy

```console
$ docker image inspect loan-api:1.0.0 --format "{{json .Config.Healthcheck}}"
{"Test":["CMD","python","-c","import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"],"Interval":30000000000,"Timeout":3000000000,"StartPeriod":10000000000,"Retries":3}

$ docker run -d --name loan-hc -p 8011:8000 loan-api:1.0.0
$ docker inspect loan-hc --format "{{.State.Health.Status}}"
healthy
$ docker ps --filter name=loan-hc --format "{{.Names}}  {{.Status}}"
loan-hc  Up 20 seconds (healthy)
```

With Compose (`api` builds from `Dockerfile.prod`, `db` is Postgres with `init.sql`):

```console
$ docker compose up -d --build
$ docker compose ps --format 'table {{.Service}}\t{{.Status}}\t{{.Ports}}'
SERVICE   STATUS                    PORTS
api       Up 15 seconds (healthy)   0.0.0.0:8000->8000/tcp
db        Up 20 seconds (healthy)   5432/tcp

$ curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
    -d '{"income":800,"loan_amount":15000,"term_months":12,"credit_score":450,"employment_years":1}'
{"score":0.9909,"risk_band":"high","decision":"reject","model_version":"1.0.0"}

$ docker compose exec -T db psql -U loan -d loans -c "SELECT id, score, risk_band, decision FROM predictions ORDER BY id;"
 id | score  | risk_band | decision
----+--------+-----------+----------
  1 | 0.3983 | medium    | approve
  2 | 0.9909 | high      | reject
(2 rows)
```

## 5. Configuration from environment variables (`MODEL_PATH`)

The model location is read from `MODEL_PATH`; nothing is hard-coded.

```console
$ grep -n "MODEL_PATH" main.py Dockerfile.prod compose.yaml
main.py:13:MODEL_PATH = os.getenv("MODEL_PATH", "model/loan_model.joblib")
main.py:25:        raise RuntimeError(f"Model file not found at MODEL_PATH={path}")
main.py:33:    state["model"] = load_model(MODEL_PATH)
Dockerfile.prod:27:    MODEL_PATH=/app/model/loan_model.joblib
compose.yaml:11:      MODEL_PATH: /app/model/loan_model.joblib
```

Changing the variable changes where the model is loaded from:

```console
$ docker run --rm -e MODEL_PATH=/app/model/missing.joblib loan-api:1.0.0
    raise RuntimeError(f"Model file not found at MODEL_PATH={path}")

$ docker run -d -p 8012:8000 -e MODEL_PATH=/models/custom.joblib \
    -v "$PWD/model/loan_model.joblib:/models/custom.joblib:ro" loan-api:1.0.0
$ docker logs <container>
INFO:loan-api:Loaded model 1.0.0 from /models/custom.joblib
```

## 6. No secrets in the image or repository, `.dockerignore` in place

`.dockerignore` keeps `.git`, virtual environments, `.env` files, keys and tests out of the build context:

```console
$ grep -E "^\.env|^\.git$|venv|tests" .dockerignore
.git
.venv/
venv/
.env
.env.*
tests/
```

Only the app and the model are in `/app`:

```console
$ docker run --rm --entrypoint ls loan-api:1.0.0 -la /app /app/model
/app:
-rw-r--r-- 1 app  app  3725 main.py
drwxr-xr-x 2 app  app  4096 model

/app/model:
-rw-r--r-- 1 app  app  1610 loan_model.joblib
```

Environment variables in the image (no passwords or tokens):

```console
$ docker image inspect loan-api:1.0.0 --format "{{range .Config.Env}}{{println .}}{{end}}"
PATH=/opt/venv/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LANG=C.UTF-8
GPG_KEY=7169605F62C751356D054A26A821E680E5FA6305
PYTHON_VERSION=3.12.16
PYTHON_SHA256=b5796915dc45ff745cfb4e990a7e7c93d6f546328a102ce31448d69ebc37575c
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
MODEL_PATH=/app/model/loan_model.joblib
```

> `GPG_KEY` comes from the official `python` base image. It is the **public** key fingerprint
> used to verify the Python download, not a secret.

Trivy secret scans of the image and the repository:

```console
$ trivy image --scanners secret --format json loan-api:1.0.0   # count of findings
image secrets found: 0

$ trivy fs --scanners secret --format json .                   # count of findings
repo secrets found: 0
```

The only credential in the repository is the development-only Postgres password in
`compose.yaml` (`loan_dev_password`), which the task allows. `.env` is in `.gitignore`.

## 7. Vulnerability scan with Trivy

### First scan (before fixing)

```console
$ trivy image --severity HIGH,CRITICAL loan-api:1.0.0
loan-api:1.0.0 (debian 13.7)   HIGH: 49   CRITICAL: 0
Python packages                HIGH: 0    CRITICAL: 0
```

Two of the 49 had a fix available: `zlib1g` CVE-2026-76844 and CVE-2026-85091
(fixed in `1:1.3.dfsg+really1.3.1-1+deb13u1`).

### Fix and rebuild

Added `apt-get update && apt-get upgrade -y` to the runtime stage of `Dockerfile.prod`, then rebuilt.

### Final scan (after rebuild)

```console
$ trivy image --severity HIGH,CRITICAL --table-mode summary loan-api:1.0.0
┌──────────────────────────────┬────────────┬─────────────────┐
│ Target                       │ Type       │ Vulnerabilities │
├──────────────────────────────┼────────────┼─────────────────┤
│ loan-api:1.0.0 (debian 13.7) │ debian     │       47        │
│ opt/venv/.../fastapi ...     │ python-pkg │        0        │
│ (all other Python packages)  │ python-pkg │        0        │
└──────────────────────────────┴────────────┴─────────────────┘
CRITICAL: 0   HIGH: 47 (all status "affected" or "fix_deferred": no fixed version published)
```

### Notes on each remaining HIGH finding

| CVE | Packages | Status | Note |
|-----|----------|--------|------|
| CVE-2026-76844, CVE-2026-85091 | zlib1g | **Fixed** | Rebuilt with `apt-get upgrade`; no longer reported. |
| CVE-2026-76642, CVE-2026-78408, CVE-2026-78409, CVE-2026-78410 | util-linux, mount, login, bsdutils, libblkid1, libmount1, libsmartcols1, libuuid1, liblastlog2-2 (36 findings) | Cannot fix yet | Debian has not released a fix. These are mount/nsenter issues; the API never calls `mount` or `nsenter` and runs as non-root without extra capabilities. |
| CVE-2025-69720 | libncursesw6, libtinfo6, ncurses-base, ncurses-bin | Cannot fix yet | No fixed version in Debian 13. The API has no terminal UI and never uses ncurses. |
| CVE-2026-119373, CVE-2026-119374, CVE-2026-119379 | libsqlite3-0 | Cannot fix yet | No fix in Debian yet. The API stores data in Postgres and never opens a SQLite database. |
| CVE-2026-16742 | libsystemd0, libudev1 | Cannot fix yet | No fix in Debian yet. systemd does not run inside the container. |
| CVE-2026-54369 | libacl1 | Cannot fix yet | No fix in Debian yet. The API does not manage file ACLs. |
| CVE-2026-9538 | perl-base | Fix deferred by Debian | Archive::Tar issue; the API never runs Perl or unpacks tar files. |

These are all part of the Debian base image and are required by the OS. The plan is to
rebuild the image as soon as Debian publishes fixes (the `apt-get upgrade` step picks them up automatically).

---

## Publish to Docker Hub (Step 3)

```bash
docker login
docker buildx build -f Dockerfile.prod \
  --platform linux/amd64,linux/arm64 \
  -t meghoing/loan-api:1.0.0 \
  -t meghoing/loan-api:latest \
  --push .
```

Docker Hub repository: `https://hub.docker.com/r/meghoing/loan-api` (tags `1.0.0` and `latest`)

## Pull and run from the registry (Step 4)

```bash
docker rmi meghoing/loan-api:1.0.0 meghoing/loan-api:latest loan-api:1.0.0
docker run --rm -p 8000:8000 meghoing/loan-api:1.0.0
```

Screenshot of `/docs` with the **200** response from `POST /predict`:

![Swagger UI showing 200 response](evidence/docs-200.png)
