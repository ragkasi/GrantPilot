FROM python:3.11-slim

WORKDIR /app

# Install system-level dependencies
# (PyMuPDF ships bundled MuPDF; no libmupdf-dev needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from pyproject.toml before copying app code
# so Docker layer caching reuses the layer on code-only changes.
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    pydantic-settings \
    python-multipart \
    httpx \
    anthropic \
    sqlalchemy \
    alembic \
    pymupdf \
    fpdf2 \
    "python-jose[cryptography]" \
    "passlib[bcrypt]" \
    bcrypt \
    email-validator \
    psycopg2-binary

# Copy application source
COPY . .

# Ensure uploads directory exists
RUN mkdir -p /app/uploads

# Copy and make the entrypoint executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
