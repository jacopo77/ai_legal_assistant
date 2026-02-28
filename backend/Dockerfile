FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
# PORT is injected by Railway at runtime; fall back to 8000 locally
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"

