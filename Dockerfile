FROM python:3.11-slim

WORKDIR /app

# Si alguna wheel no existe (bcrypt/psycopg2), quizá necesites build tools:
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Vars útiles
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV PORT=5000
ENV REDIS_URL="redis://redis:6379/0"
ENV APP_STATE_DIR="/state"

# Prepara carpeta de estado (para preguntas.json, fichas, notas, logs, etc.)
RUN mkdir -p /state

EXPOSE 5000

# Asegúrate de que el script exista y sea ejecutable
RUN chmod +x /app/entrypoint.sh
CMD ["/app/entrypoint.sh"]
