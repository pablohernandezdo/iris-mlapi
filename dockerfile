# ---- base stage ----
FROM python:3.13-slim-bookworm AS base

# Env config
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# System deps + Microsoft ODBC repo + ODBC Driver 18
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg2 apt-transport-https \
    unixodbc unixodbc-dev \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# ---- dev stage ----
FROM base AS dev

# Azure CLI — needed for DefaultAzureCredential (AzureCliCredential) in local dev.
# Not included in prod or test stages.
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install package in editable mode
RUN pip install --no-cache-dir -e .

# Install pinned dev/test tools
COPY requirements.dev.txt .
RUN pip install --no-cache-dir -r requirements.dev.txt

# Switch user
USER appuser

# Expose app + debug ports
EXPOSE 8000
EXPOSE 5678

# Run with debugger + reload
CMD ["python", "-m", "debugpy", \
     "--listen", "0.0.0.0:5678", \
     "--wait-for-client", \
     "-m", "uvicorn", "ml_api.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---- prod stage ----
FROM base AS prod

# Install package
RUN pip install --no-cache-dir .

# Strip test files — copied by base's COPY . . but don't belong in prod
RUN rm -rf src/tests/

# Switch user
USER appuser

# Expose port
EXPOSE 8000

# Run production server
# CMD ["tail", "-f", "/dev/null"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", \
     "ml_api.main:app", "--bind", "0.0.0.0:8000"]

# ---- test stage ----
# Same installed package as prod; adds test tools and test source only.
FROM prod AS test

USER root
COPY requirements.dev.txt .
RUN pip install --no-cache-dir -r requirements.dev.txt
# Re-add test files that prod stripped out
COPY src/tests/ src/tests/

USER appuser