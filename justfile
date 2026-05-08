# ---------- Local ----------
install:
    uv pip install -e .

run:
    just install
    uv run uvicorn ml_api.main:app --reload

lint:
    uv run ruff check src/
    uv run ruff format src/

# ---------- Helpers ----------

wait-db:
    @bash -c '\
    echo "Waiting for DB..."; \
    until bash -c "echo > /dev/tcp/localhost/1433" 2>/dev/null; do \
        sleep 2; \
    done; \
    echo "DB is healthy!"'

# ---------- Core workflow ----------

dev:
    docker compose up -d sqlserver
    just wait-db
    docker compose run --rm migrate
    docker compose up -d app

rebuild:
    docker compose down --remove-orphans
    docker compose build --no-cache
    just dev

reset:
    docker compose down --volumes --remove-orphans
    docker compose build --no-cache
    just dev

down:
    docker compose down

restart:
    docker compose restart app

freeze:
    @uv export --no-dev -o requirements.txt > /dev/null

freeze-dev:
    @uv export --only-group dev -o requirements.dev.txt > /dev/null

# ---------- Infrastructure ----------

# Provision Azure infrastructure.
# Usage: just infra-deploy <sql-admin-password>
# Example: just infra-deploy 'MyStr0ngPassw0rd'
infra-deploy sql_admin_password:
    @SQL_ADMIN_PASSWORD='{{ sql_admin_password }}' az deployment group create \
        --resource-group rg-mlapi-prod \
        --template-file infra/main.bicep \
        --parameters infra/main.bicepparam

# ---------- Logs & Debug ----------

logs:
    docker compose logs -f app

debug:
    docker compose -f docker-compose.debug.yml up -d

shell:
    docker compose exec app sh

build:
    docker compose build

build-ci:
    docker compose -f docker-compose.yml -f docker-compose.ci.yml build

# ---------- Testing ----------
test-unit:
    uv run pytest src/tests/unit/ -v

# Inner recipes — no build, no DB startup. Called by test / test-ci after
# a single shared build so the image is not rebuilt for every suite.
_run-integration:
    docker compose up -d sqlserver
    just wait-db
    docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm migrate
    docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm app python -m pytest src/tests/integration/ -v -p no:cacheprovider

_run-integration-ci:
    docker compose up -d sqlserver
    just wait-db
    docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.test.yml run --rm migrate
    docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.test.yml run --rm app python -m pytest src/tests/integration/ -v -p no:cacheprovider

_run-e2e:
    docker compose up -d sqlserver
    just wait-db
    docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm migrate
    docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm app python -m pytest src/tests/e2e/ -v -p no:cacheprovider

_run-e2e-ci:
    docker compose up -d sqlserver
    just wait-db
    docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.test.yml run --rm migrate
    docker compose -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.test.yml run --rm app python -m pytest src/tests/e2e/ -v -p no:cacheprovider

# Standalone recipes — build once then run. Useful when running a single suite.
test-integration:
    just build
    just _run-integration

test-integration-ci:
    just build-ci
    just _run-integration-ci

test-e2e:
    just build
    just _run-e2e

test-e2e-ci:
    just build-ci
    just _run-e2e-ci

# Full suites — build once, run all suites against that image.
test:
    just test-unit
    just build
    just _run-integration
    just _run-e2e

test-ci:
    just test-unit
    just build-ci
    just _run-integration-ci
    just _run-e2e-ci

# ---------- Migrations ----------

makemigration name:
    docker compose run --rm migrate alembic revision --autogenerate -m "{{name}}"

migrate:
    docker compose run --rm migrate alembic upgrade head

downgrade:
    docker compose run --rm migrate alembic downgrade -1

# ---------- System ----------

prune:
    docker system prune -a --volumes
