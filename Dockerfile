FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 💡 Asegura importación correcta desde /app
ENV PYTHONPATH="/app"

# ✅ Para que print() se muestre inmediatamente
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

RUN pip install gunicorn

# ✅ Logs de acceso y error a consola + verbose
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "www.app:app", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "debug"]
