# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /code

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runner

WORKDIR /code

# Copy only installed packages from builder
COPY --from=builder /root/.local /root/.local
COPY app /code/app
COPY data /code/data

# Ensure scripts in .local/bin are in PATH
ENV PATH=/root/.local/bin:$PATH

# Environment variables should be provided at runtime
EXPOSE 8000

# Use non-root user for security
RUN useradd -m appuser && chown -R appuser /code
USER appuser

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]