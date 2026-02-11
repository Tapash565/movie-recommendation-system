FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /code/app
COPY data /code/data

# Environment variables should be provided at runtime via:
# - docker run -e VAR=value
# - docker-compose env_file or environment
# - Orchestration platform secrets (Kubernetes, AWS ECS, etc.)
# Never copy .env files into the image to avoid baking secrets into layers

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]