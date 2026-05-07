# iris-mlapi

A production-style FastAPI ML inference API that serves an iris classification model.

## Architecture

- **API**: FastAPI with lifespan pattern, pydantic-settings, structured logging
- **Model**: scikit-learn pipeline loaded from Azure Blob Storage at startup via `DefaultAzureCredential`
- **Database**: SQL Server (Docker locally, Azure SQL in production) — predictions persisted via SQLAlchemy 2.0 + Alembic
- **Compute**: Azure Container Apps (scale-to-zero, revision-based deploys)
- **Auth**: Managed identity throughout — no stored credentials anywhere

## Local development

```bash
cp .env.example .env   # fill in your values
just dev               # starts SQL Server, runs migrations, starts app
```

The app is available at `http://localhost:8000`. Interactive docs at `/docs`.

## Running tests

```bash
just test-unit          # fast, no Docker
just test-integration   # requires Docker + SQL Server
just test-e2e           # requires Docker + SQL Server
just test               # all three
just test-ci            # CI mode (uses test Docker stage, no volume mounts)
```

## Provisioning infrastructure

One-time setup — creates ACR, Azure SQL, Key Vault, Container Apps, and managed identities:

```bash
az group create --name rg-mlapi-prod --location eastus
just infra-deploy 'YourPassword'
```

Outputs from the deployment map directly to the GitHub repository secrets required by the CI/CD pipeline.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/health/ready` | Readiness check (DB + model) |
| `POST` | `/predict` | Run inference, persist result |
| `GET` | `/predictions` | Query saved predictions |

### Example prediction request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
```
