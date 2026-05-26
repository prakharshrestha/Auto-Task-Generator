FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# system deps (add more if your requirements need them)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

COPY backend/ /app/backend/
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8000

# Adjust module path if your app entry differs
# Common FastAPI: backend/main.py has app = FastAPI()
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host=0.0.0.0", "--port=8000"]
