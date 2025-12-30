#!/usr/bin/env python3
import os
import json
import glob
from redis import Redis


def get_conn():
    url = (os.environ.get('REDIS_URL') or '').strip()
    if url and '<' not in url and '>' not in url:
        return Redis.from_url(url)
    host = os.environ.get('REDISHOST')
    port = int(os.environ.get('REDISPORT', 6379))
    user = os.environ.get('REDISUSER', 'default')
    pwd = os.environ.get('REDISPASSWORD') or os.environ.get('REDIS_PASSWORD')
    return Redis(host=host, port=port, username=user, password=pwd)


def migrate():
    base = os.path.join(os.path.dirname(__file__), 'www', 'admin', 'logs')
    conn = get_conn()
    files = glob.glob(os.path.join(base, '*.json'))
    if not files:
        print('No log files found in', base)
        return
    for fpath in files:
        name = os.path.splitext(os.path.basename(fpath))[0]
        try:
            with open(fpath, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception as e:
            print('Skipping', fpath, 'read error:', e)
            continue
        if not isinstance(data, list) or not data:
            print('No events for', name)
            continue
        key = f'logs:{name}'
        count = 0
        for item in data:
            try:
                conn.rpush(key, json.dumps(item, ensure_ascii=False))
                count += 1
            except Exception as e:
                print('Error pushing item for', name, e)
        print(f'Migrated {count} events -> {key}')


if __name__ == '__main__':
    migrate()
