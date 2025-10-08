# MinervaPrimeNSE/worker.py
import os
import sys
from urllib.parse import urlparse

from redis import Redis
from rq import Worker, Queue


def get_redis_conn() -> Redis:
    """
    Crea la conexión a Redis. Prioriza REDIS_URL (Railway Reference).
    Como fallback opcional, usa REDISHOST/REDISPORT/REDISUSER/REDISPASSWORD.
    """
    url = os.environ.get("REDIS_URL")
    if url:
        url = url.strip()
        parsed = urlparse(url)
        print(f"[Worker] Using REDIS_URL host={parsed.hostname} port={parsed.port} user={parsed.username} scheme={parsed.scheme}", flush=True)
        kwargs = {}
        # Si algún proveedor usa TLS con cert autofirmado:
        if parsed.scheme == "rediss":
            kwargs["ssl_cert_reqs"] = None
        return Redis.from_url(url, **kwargs)

    # ---- Fallback con variables separadas (opcional) ----
    host = os.environ.get("REDISHOST")
    port = int(os.environ.get("REDISPORT", 6379))
    user = os.environ.get("REDISUSER", "default")
    pwd  = os.environ.get("REDISPASSWORD")
    if host and pwd:
        print(f"[Worker] Using discrete Redis vars host={host} port={port} user={user}", flush=True)
        return Redis(host=host, port=port, username=user, password=pwd)

    print("[Worker] ERROR: No Redis credentials found. Define REDIS_URL (recommended).", file=sys.stderr, flush=True)
    sys.exit(1)


def main():
    conn = get_redis_conn()

    # Prueba temprana
    try:
        conn.ping()
        print("[Worker] Redis ping OK", flush=True)
    except Exception as e:
        print(f"[Worker] Redis ping FAILED: {e}", file=sys.stderr, flush=True)
        sys.exit(2)

    # Colas a escuchar
    listen = os.getenv("RQ_QUEUES", "queries").split(",")
    listen = [q.strip() for q in listen if q.strip()]
    if not listen:
        listen = ["queries"]

    queues = [Queue(name, connection=conn) for name in listen]
    print(f"[Worker] Listening queues: {listen}", flush=True)

    # Arranca el worker (con scheduler)
    worker = Worker(queues, connection=conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
