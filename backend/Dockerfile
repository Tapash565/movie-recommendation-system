# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /code

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runner

# Use non-root user for security
RUN useradd -m appuser

WORKDIR /code
RUN chown appuser:appuser /code

# Copy only installed packages from builder, and chown to appuser
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser app /code/app
COPY --chown=appuser:appuser data /code/data

# Ensure scripts in .local/bin are in PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Environment variables should be provided at runtime
EXPOSE 8000

USER appuser

CMD ["sh", "-c", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:${PORT:-8000}"]