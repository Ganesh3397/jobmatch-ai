# ---------- Production image: builds React and serves it from Django (one URL) ----------
# Stage 1: build the React frontend
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Django backend + built frontend
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY sample_resumes/ /sample_resumes/
COPY --from=frontend /app/dist ./frontend_build
RUN DEBUG=False SECRET_KEY=build-only USE_REDIS=False DB_ENGINE=sqlite python manage.py collectstatic --noinput
RUN chmod +x start.sh
EXPOSE 8000
CMD ["./start.sh"]
