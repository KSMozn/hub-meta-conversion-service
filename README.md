# Hub Meta Conversion Service

FastAPI service that the Hub uses to sync Meta Ads pixels and programmatically create conversion tags (custom conversions) on behalf of advertisers. It is the production-style replacement for the legacy ETL job that read Meta data into the Hub once a day with no write path.

## What it does

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/advertisers` | Register an advertiser the Hub manages. |
| `GET` | `/advertisers/{advertiser_id}` | Read an advertiser. |
| `POST` | `/integrations/meta/sync-pixels` | Pull all pixels from Meta for an advertiser and upsert them. |
| `GET` | `/advertisers/{advertiser_id}/pixels` | List the pixels we've synced. |
| `POST` | `/advertisers/{advertiser_id}/conversion-tags` | Create a Hub conversion tag **and** the matching custom conversion in Meta. |
| `GET` | `/advertisers/{advertiser_id}/conversion-tags` | List conversion tags for an advertiser. |
| `GET` | `/healthz`, `/readyz` | Liveness/readiness for Cloud Run. |

`POST /advertisers/{id}/conversion-tags` honors the `Idempotency-Key` header. Replays with the same body return the cached `201`; replays with a *different* body return `409 idempotency_conflict`.

## How this maps to the production use case

* The Hub already syncs Meta Ads performance data via ETL. This service is the **first FastAPI endpoint that writes back to Meta**, and it's the template for every future write integration (Google Ads, TikTok, etc.).
* The adapter pattern (`app/integrations/meta/adapter.py`) is the contract every platform integration must satisfy. The mock adapter lives next to the real one and is the test seam — services depend on the `MetaAdapter` protocol, not on either implementation.
* OAuth tokens are stored encrypted-at-rest per `(advertiser, provider)`. The refresh path is centralized in `OAuthService` so every adapter calls Meta with a fresh token without each integration re-implementing refresh.
* Idempotency is a service-wide concern, not a per-endpoint hack. The `idempotency_records` table is shared across endpoints — only the endpoint discriminator changes.

## Local quickstart

Requires Python 3.13 and Docker (for the Postgres testcontainer in the integration tests).

```bash
# Install deps
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Bring up Postgres + the API
cp .env.example .env
docker compose up --build

# OR run the API directly
docker compose up -d postgres
export $(grep -v '^#' .env | xargs)
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

Open http://localhost:8080/docs.

### Example session

```bash
curl -s -X POST localhost:8080/advertisers \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme","external_ref":"acme-1","meta_business_id":"biz_1","meta_ad_account_id":"act_42"}'
# {"id":"…","name":"Acme",…}

# (TBD: a real OAuth bootstrap endpoint — for the POC, seed the token via OAuthService.)

curl -s -X POST localhost:8080/integrations/meta/sync-pixels \
  -H 'Content-Type: application/json' \
  -d '{"advertiser_id":"<id>"}'

curl -s -X POST "localhost:8080/advertisers/<id>/conversion-tags" \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: 2026-06-17-purchase-USD' \
  -d '{"pixel_id":"<pixel-uuid>","name":"Purchase USD","event_type":"Purchase","category":"purchase","value":"29.99","currency":"USD"}'
```

## Tests

```bash
pytest                           # unit + integration (integration needs Docker)
pytest tests/unit                # unit only
pytest -k "idempotency or retry" # subset
```

Integration tests spin up a real Postgres via `testcontainers`. They are auto-skipped when Docker isn't running so they don't break CI on machines without Docker.

## Project layout

```
app/
  main.py                FastAPI app factory.
  api/
    deps.py              Wires services into request handlers.
    errors.py            Service exceptions → HTTP responses.
    routes/              advertisers, integrations, conversion_tags, health.
  core/
    config.py            Pydantic Settings.
    security.py          TokenCipher for OAuth tokens at rest.
    logging.py           JSON logging for Cloud Logging.
  db/
    base.py              Declarative base + naming convention.
    session.py           Engine/session lifecycle.
  models/                SQLAlchemy ORM.
  schemas/               Pydantic request/response models.
  repositories/          Thin data-access objects (no business logic).
  services/              Business logic; transactions begin and end here.
  integrations/meta/
    adapter.py           The Protocol the rest of the app depends on.
    mock_adapter.py      Deterministic in-memory fake used in dev/tests.
    real_adapter.py      Production Marketing API calls.
    client.py            httpx client with tenacity-backed retries.
    schemas.py           Wire models for Meta.
alembic/                 Migrations.
tests/
  unit/                  No DB required.
  integration/           testcontainers Postgres.
terraform/
  modules/               Reusable modules (Cloud Run, Cloud SQL, Secret Manager, Scheduler).
  terragrunt/            Per-env wiring.
Dockerfile
docker-compose.yml
```

## Replacing the mock Meta adapter with the real one

Everything depends on the `MetaAdapter` Protocol in [app/integrations/meta/adapter.py](app/integrations/meta/adapter.py). To go live:

1. **Flip `META_USE_MOCK=false`.** `create_app()` then constructs `RealMetaAdapter(MetaApiClient(settings))` instead of `MockMetaAdapter`. No other code path changes.
2. **Set `META_API_BASE_URL`** (e.g. `https://graph.facebook.com/v20.0`).
3. **Provision OAuth tokens** for each advertiser. The current `OAuthService._refresh_with_provider` is a stub that returns a deterministic mock access token; replace it with a real `POST /oauth/access_token` call (`grant_type=fb_exchange_token` for long-lived tokens) and parse `access_token` / `expires_in` into the existing return tuple. The rest of the refresh path is unchanged.
4. **Validate `RealMetaAdapter` against a sandbox ad account.** The two API surfaces it covers are:
   * `GET /{ad_account_id}/adspixels?fields=id,name,status`
   * `POST /{ad_account_id}/customconversions`

   Both already shape Meta's response/payload exactly; if Meta adds required fields they get added in `schemas.py` and the call sites in one place.
5. **Retry behavior:** the client retries on `429` and 5xx via tenacity (`META_MAX_RETRIES`, `META_RETRY_BASE_DELAY_SECONDS`). `Retry-After` is honored as a hint. `401/403` is mapped to `MetaAuthError` and *not* retried — the OAuth refresh path catches it on the next request.

## Production checklist

* [ ] Replace `TokenCipher` (`app/core/security.py`) with a Cloud KMS envelope encryption helper or Fernet. The repository contract (string → string) stays the same.
* [ ] Replace `OAuthService._refresh_with_provider` with a real Meta OAuth call.
* [ ] Add a periodic job (Cloud Scheduler is wired in `terraform/modules/scheduler_pixel_sync`) to expire stale idempotency records.
* [ ] Add Cloud Trace + OpenTelemetry instrumentation; the JSON log format already plays nicely with Cloud Logging severity.
* [ ] Tighten Cloud Run ingress to internal + VPC connector once the Hub frontend is also behind the same VPC.

## Deployment (GCP)

The Terraform modules under [terraform/modules/](terraform/modules/) are pieced together by Terragrunt in [terraform/terragrunt/](terraform/terragrunt/). Per environment you get:

* **Cloud SQL Postgres 16** (`modules/cloud_sql`) with private IP, PITR backups.
* **Secret Manager** entries (`modules/secrets`) for `DATABASE_URL`, `TOKEN_ENCRYPTION_KEY`, `META_OAUTH_CLIENT_SECRET`, with `roles/secretmanager.secretAccessor` granted to the service account.
* **Cloud Run v2 service** (`modules/cloud_run_service`) consuming those secrets via `value_source.secret_key_ref`, with a startup probe on `/healthz`.
* **Cloud Scheduler job** (`modules/scheduler_pixel_sync`) that POSTs to `/integrations/meta/sync-pixels` on a cron, authenticated with an OIDC token.

To plan/apply a single environment:

```bash
cd terraform/terragrunt/dev/cloud_run
terragrunt plan
terragrunt apply
```

`terragrunt run-all apply` from `terraform/terragrunt/dev/` applies everything respecting `dependency` blocks (secrets → cloud_sql → cloud_run → scheduler).

## Conventions

* Service-layer functions raise `NotFoundError`/`ConflictError`/`UpstreamError`. Handlers in `app/api/errors.py` map those to HTTP codes — routers never raise `HTTPException` directly.
* Repositories never commit; the session yielded by `get_session` commits once per request after the route returns.
* Anything that calls Meta goes through `MetaAdapter`. Adding a new operation = one method on the Protocol + both implementations.
