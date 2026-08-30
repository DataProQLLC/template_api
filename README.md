# template_api

FastAPI template for a mobile backend. Supabase/PostgREST for data, deployed to Google Cloud Run.

Multi-version (`/v1`, `/v2`) in a **single** deployment, JWT verification via JWKS, one error shape everywhere, pinned + hashed dependencies.

```
deployables/core/         one deployable unit (one Cloud Run service)
  app/
    api/
      deps.py             shared FastAPI dependencies (auth, db)
      v1/, v2/            one package per API version
        routes/           HTTP layer: status codes, validation
        schemas/          versioned request/response contracts
    services/             business logic (NOT versioned; reused across versions)
    repositories/         data access -- the only layer that knows PostgREST
    clients/              outbound vendor APIs (sync SDKs quarantined here)
    config.py             per-deployable settings
    main.py               app assembly, version mounting, lifespan
  Dockerfile
shared/                   code shared by every deployable
  api/                    middleware, pagination, status endpoint
  auth/                   JWKS cache + bearer token verification
  config/                 base settings, environment URL derivation
  db/                     async PostgREST client
  docs/                   Swagger UI with the version selector
  errors/                 exception types + unified handlers
requirements.in           dependencies you edit
requirements.txt          generated lockfile -- never edit by hand
```

---

## 1. Local setup

### Prerequisites

| Tool | Why | Install |
|---|---|---|
| **Python 3.11** | Matches the Dockerfile. 3.12+ works but diverges from prod. | `brew install python@3.11` |
| **uv** | Compiles the dependency lockfile. | `brew install uv` |
| **Docker Desktop** | Only to test the container before deploying. | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **gcloud CLI** | Only for deploying. | `brew install --cask google-cloud-sdk` |
| **Caddy** | Optional. Local HTTPS at `api.local.<app>.com`. | `brew install caddy` |

VS Code: install the Python extension, then **Cmd+Shift+P → Python: Select Interpreter → `./.venv/bin/python`**. Without this, VS Code lints against the wrong interpreter and shows phantom import errors.

### First run

```bash
git clone https://github.com/DataProQLLC/template_api.git
cd template_api

python3.11 -m venv .venv
source .venv/bin/activate
make install                     # installs from the pinned, hashed lockfile

mkdir -p secrets
cp secrets/.env.core.example secrets/.env.core   # then fill in real values
```

`secrets/` is gitignored. Required values (Supabase dashboard → Project Settings → API):

```bash
DB_URL=https://<project-ref>.supabase.co
DB_PUBLISHABLE_KEY=sb_publishable_...   # safe in clients; RLS applies
DB_SECRET_KEY=sb_secret_...             # SERVER ONLY -- bypasses RLS entirely
```

Then:

```bash
make core                        # -> http://127.0.0.1:8080/docs
```

### Optional: HTTPS with production-shaped URLs

Makes local look like dev and prod (`https://api.local.template.com/v2/...`), so you catch hostname and TLS problems before deploying.

```bash
brew install caddy
make hosts                       # one-time, adds /etc/hosts entry (sudo)
make proxy                       # terminal 1 -- Caddy on :443
make core                        # terminal 2 -- uvicorn on :8080
```

Open `https://api.local.template.com/docs`. Caddy issues a locally-trusted cert on first run.

> **Match the origin you browse to the Servers dropdown.** On `127.0.0.1:8080/docs`, pick `127.0.0.1 (no proxy)`. Mismatched origin means the browser makes a cross-origin request, which fails CORS with "Failed to fetch". Not a server bug.

### Make targets

| Command | Does |
|---|---|
| `make install` | Install from `requirements.txt` with hash verification |
| `make lock` | Recompile the lockfile after editing `requirements.in` |
| `make core` | Run the core deployable on :8080 with hot reload |
| `make run SVC=x PORT=n` | Run any other deployable |
| `make hosts` / `make unhosts` | Add/remove the local hostname |
| `make proxy` | Run Caddy |

### Adding a dependency

Never edit `requirements.txt` — it's generated.

```bash
echo 'some-package>=1.2' >> requirements.in
make lock
make install
git add requirements.in requirements.txt
```

---

## 2. Endpoints

| Path | Versioned | Purpose |
|---|---|---|
| `/health` | No | Liveness probe. Checks nothing, never breaks. |
| `/` | No | Version index. |
| `/docs` | No | Swagger UI. Version dropdown + environment dropdown. Hidden in prod. |
| `/{version}/status` | Yes | Deprecation state, runtime capacity, server time. |
| `/{version}/auth/*` | Yes | Auth. |
| `/{version}/debug/*` | Yes | Load-testing endpoints. **Never registered in prod.** |

`/health` deliberately checks no dependencies. If it queried the database, a slow database would fail the probe, Cloud Run would kill healthy instances, and a degradation would become an outage.

`/{version}/status` is the one your mobile app calls on launch:

```json
{
  "version": "v1",
  "latest_version": "v2",
  "supported_versions": ["v1", "v2"],
  "deprecated": true,
  "sunset": "2027-01-01",
  "deployment": {"instance": "dd74b809", "revision": "core-00042-abc", "uptime_seconds": 331.2},
  "runtime": {"threadpool_total": 40, "threadpool_available": 40},
  "server_time": "2026-08-30T03:58:48Z"
}
```

`deprecated` + `sunset` drive an in-app upgrade prompt without shipping a build. `threadpool_available` at 0 means sync handlers are queueing. `server_time` lets a client detect clock skew, the usual cause of spurious "token expired" errors.

---

## 3. Response conventions

### Errors — one shape, always

Every failure returns the same body, including 401s, validation errors, 404s and unhandled 500s:

```json
{
  "error": {
    "code": "validation_failed",
    "message": "One or more fields are invalid.",
    "details": [{"field": "email", "message": "value is not a valid email address", "type": "value_error"}],
    "request_id": "2e92f39e-b8b9-4744-a498-f7f320dacfe1"
  }
}
```

- **Branch on `code`, never `message`.** Codes are stable; messages get reworded and localised without a version bump.
- `details` appears only for field-level validation errors.
- `request_id` is echoed in the `X-Request-ID` header and written to every log line. Send an inbound `X-Request-ID` to trace a request end to end from the client.
- Unhandled exceptions log the real traceback server-side and return only the generic message plus the id. Internals never reach the client.

Codes: `bad_request`, `invalid_credentials`, `forbidden`, `not_found`, `method_not_allowed`, `conflict`, `validation_failed`, `rate_limited`, `internal_error`, `upstream_unavailable`, `upstream_timeout`.

> A CORS failure is **not** one of these. The browser discards the response before your code sees it, and a rejected preflight never reaches a handler. No server-side error shape can fix "Failed to fetch" — fix the origin mismatch instead.

### Success — bare singles, wrapped collections

```
GET /v2/auth/me   ->  {"id": "...", "username": "..."}
GET /v2/items     ->  {"data": [...], "meta": {...}}
```

```json
{
  "data": [{"id": "1"}, {"id": "2"}],
  "meta": {"limit": 50, "offset": 0, "count": 2, "total": 137, "has_more": true, "next_offset": 2}
}
```

Wrapping single resources too (JSON:API style) is defensible, but it adds nesting to every client model for metadata only collections have. What matters most is **consistency within a version** — don't mix styles.

Use the helpers in `shared/api/responses.py`:

```python
from shared.api.responses import Page, PageParams, ERROR_RESPONSES

@router.get("/items", response_model=Page[Item], responses=ERROR_RESPONSES)
async def list_items(db: Db, page: Annotated[PageParams, Depends()]):
    rows, total = await repo.list_items(db, limit=page.limit, offset=page.offset)
    return Page.of(rows, limit=page.limit, offset=page.offset, total=total)
```

`total` is optional — omit it when counting is expensive and `has_more` is inferred from a full page.

---

## 4. Versioning

Versions are **URL prefixes inside one deployment**, not separate services. `/v1` and `/v2` run in the same container, same Cloud Run service, same `gcloud run deploy`.

Registered in one place, `deployables/core/app/main.py`:

```python
VERSIONS = [
    ("v1", v1_router, "Maintenance only.", True,  None),   # deprecated
    ("v2", v2_router, "Current version.",  False, None),
]
```

The tuple is `(name, router, description, deprecated, sunset)`. Everything derives from this list: mounts, `/health`, `/status`, the docs version dropdown.

**Bump the version only for breaking changes.** Most changes shouldn't need one:

| Additive — no bump | Breaking — bump |
|---|---|
| New endpoint | Removing or renaming a field |
| New optional request field | Changing a field's type |
| New response field | Making an optional field required |
| | Changing status codes or error semantics |

Adding an enum value is often breaking if clients parse strictly — Dart enums throw on unknown values.

**When you do bump, bump the whole surface, but reuse unchanged handlers:**

```python
# app/api/v2/routes/auth.py
from app.api.v1.routes.auth import signup, signin, refresh

router.add_api_route("/signup", signup, methods=["POST"], status_code=201)
```

A v2 client gets a complete surface; there's still one implementation of each unchanged handler.

**Retiring a version:** set `deprecated=True` and a `sunset` date, watch `/v1` traffic in Cloud Run metrics until it approaches zero, then delete the line and the `app/api/v1` package.

---

## 5. Deploying to Cloud Run

Both versions ship together. There is no per-version deploy.

### One-time project setup

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com

gcloud artifacts repositories create app \
  --repository-format=docker --location=us-east4
```

### Secrets

Never pass `DB_SECRET_KEY` via `--set-env-vars` — it's visible in the service description and in deploy logs.

```bash
echo -n "sb_secret_..." | gcloud secrets create db-secret-key-dev --data-file=-
echo -n "sb_publishable_..." | gcloud secrets create db-publishable-key-dev --data-file=-

PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')
for s in db-secret-key-dev db-publishable-key-dev; do
  gcloud secrets add-iam-policy-binding $s \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

### Build and deploy

Build context is the **repo root** (the Dockerfile copies both `shared/` and `deployables/core/app/`).

```bash
REGION=us-east4
IMAGE=$REGION-docker.pkg.dev/YOUR_PROJECT_ID/app/core
TAG=$(git rev-parse --short HEAD)

gcloud builds submit --tag $IMAGE:$TAG .

gcloud run deploy core-dev \
  --image $IMAGE:$TAG \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars ENV=dev,APP_NAME=template,LOG_LEVEL=INFO,DB_URL=https://your-dev-ref.supabase.co \
  --set-secrets DB_SECRET_KEY=db-secret-key-dev:latest,DB_PUBLISHABLE_KEY=db-publishable-key-dev:latest \
  --concurrency 80 \
  --timeout 300 \
  --min-instances 0 \
  --cpu 1 --memory 512Mi
```

Verify both versions are live on the one service:

```bash
URL=$(gcloud run services describe core-dev --region $REGION --format='value(status.url)')
curl -s $URL/health         # {"ok":true,"versions":["v1","v2"],"latest":"v2"}
curl -s $URL/v1/status      # {"version":"v1","deprecated":true,...}
curl -s $URL/v2/status      # {"version":"v2","deprecated":false,...}
```

Tag images with the git SHA, not `latest` — Cloud Run resolves the digest at deploy time, so `latest` makes rollbacks ambiguous.

### Settings that matter

| Flag | Why |
|---|---|
| `--concurrency 80` | Default. Requests per instance before scaling out. Do **not** set to 1 — that serialises everything. |
| `--timeout 300` | Max seconds per request (ceiling 3600). |
| `--min-instances 1` | Prod only. Avoids cold starts on the auth path; costs an always-on instance. |
| `--set-env-vars ENV=prod` | Disables `/docs`, `/openapi.json`, and all `/debug` routes. |

`ENV` is the single most important variable. With `ENV=prod` the docs and debug endpoints don't exist at all.

### Per environment

Separate Cloud Run services, ideally separate GCP projects, always separate Supabase projects:

```bash
core-dev     ENV=dev     -> api.dev.template.com
core-stage   ENV=stage   -> api.stage.template.com
core-prod    ENV=prod    -> api.template.com
```

### Custom domains

One hostname to one service — Cloud Run domain mapping is enough:

```bash
gcloud run domain-mappings create --service core-dev \
  --domain api.dev.template.com --region $REGION
```

It prints DNS records to add at your registrar. Verify the domain first at [Search Console](https://search.google.com/search-console). Managed certificates take ~15 minutes.

Add a global external Application Load Balancer only when you need **path-based routing across services** (`/v1/ingest/*` to a different deployable) or Cloud Armor. Roughly $20/month before traffic.

> Whatever sits in front, **do not strip the path prefix.** Let `/v2/auth/me` reach the container unchanged. Rewriting requires setting FastAPI's `root_path` to match and breaks the docs. The `Caddyfile` mirrors this locally.

### Testing before deploy

```bash
docker build -f deployables/core/Dockerfile -t core .
docker run --rm -p 8080:8080 --env-file secrets/.env.core -e ENV=local core
curl localhost:8080/health
```

Confirm prod hides what it should:

```bash
docker run --rm -p 8080:8080 --env-file secrets/.env.core -e ENV=prod core
curl -s -o /dev/null -w '%{http_code}\n' localhost:8080/docs          # 404
curl -s -o /dev/null -w '%{http_code}\n' localhost:8080/v2/debug/fast # 404
```

### Rollback

```bash
gcloud run revisions list --service core-prod --region $REGION
gcloud run services update-traffic core-prod --region $REGION --to-revisions REVISION=100
```

---

## 6. Concurrency rules

Every handler is `async def`, every I/O call is awaited. Mixing is the one thing that will take down the service:

| Pattern | Result |
|---|---|
| `async def` + `await` | Correct. Full concurrency. |
| `def` + blocking call | Correct. Threadpool, caps at 40 concurrent. |
| **`async def` + blocking call** | **Stalls the event loop for every user on that instance.** |

A sync-only vendor SDK goes behind an async facade in `app/clients/`, and `anyio.to_thread` appears nowhere else:

```python
async def transactions_get(...):
    return await anyio.to_thread.run_sync(lambda: _client().transactions_get(req))
```

Demonstrate the difference on a deployed dev service:

```bash
python loadtest.py https://core-dev-xxxx.us-east4.run.app 20 15
```

`/debug/slow-blocking` serialises; the others don't.

---

## 7. Adding a deployable

`deployables/` holds independently deployable units — each becomes its own Cloud Run service.

Add one only for a real reason: different scaling profile (a webhook ingester), different runtime shape (a queue consumer), independently owned tables, or a different security posture. **Not** because a feature calls a vendor API — that's a `clients/` module inside the service that owns the domain.

```
deployables/ingest/
  Dockerfile
  app/{main.py,config.py,api/,services/,repositories/,clients/}
```

Then `make run SVC=ingest PORT=8081`.