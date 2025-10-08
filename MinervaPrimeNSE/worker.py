# MinervaPrimeNSE/worker.py
import os
from redis import Redis
from rq import Worker, Queue

listen = os.getenv('RQ_QUEUES', 'queries').split(',')
REDIS_URL = os.environ["REDIS_URL"]
conn = Redis.from_url(REDIS_URL)

print(f"[Worker] Redis host: {conn.connection_pool.connection_kwargs.get('host')}", flush=True)

if __name__ == '__main__':
    queues = [Queue(name, connection=conn) for name in listen]
    worker = Worker(queues, connection=conn)
    worker.work(with_scheduler=True)
    print("Worker started, listening to queues:", listen)