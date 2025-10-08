# MinervaPrimeNSE/worker.py
import os
from redis import Redis
from rq import Worker, Queue

listen = os.getenv('RQ_QUEUES', 'queries').split(',')
redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    queues = [Queue(name, connection=conn) for name in listen]
    worker = Worker(queues, connection=conn)
    worker.work(with_scheduler=True)
    print("Worker started, listening to queues:", listen)