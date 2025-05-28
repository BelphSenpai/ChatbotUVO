FROM python:3.11-slim

WORKDIR /app

# Copia primero requirements e instala dependencias
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ⬅️ Copia TODO el proyecto, no solo /www
COPY . .

# Asegura que Gunicorn pueda importar desde /app
ENV PYTHONPATH="${PYTHONPATH}:/app"

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "www.app:app"]
