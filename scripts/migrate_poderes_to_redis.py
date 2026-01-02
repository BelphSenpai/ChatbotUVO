#!/usr/bin/env python3
"""Migra snapshots de poderes (www/poderes/usuarios/*.txt) a Redis.
Uso: setear REDIS_URL o REDISHOST/REDISPASSWORD etc. y ejecutar.
"""
import os
from MinervaPrimeNSE.worker import get_redis_conn

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PODERES_DIR = os.path.join(BASE_DIR, 'www', 'poderes', 'usuarios')


def main():
    conn = get_redis_conn()
    if not os.path.isdir(PODERES_DIR):
        print("No existe directorio de poderes:", PODERES_DIR)
        return

    migrated = 0
    for fname in os.listdir(PODERES_DIR):
        if not fname.endswith('.txt'):
            continue
        user = os.path.splitext(fname)[0]
        ruta = os.path.join(PODERES_DIR, fname)
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            key = f"poderes:{user}"
            conn.set(key, contenido or "")
            migrated += 1
            print(f"Migrado {user}")
        except Exception as e:
            print(f"Error migrando {ruta}: {e}")

    print(f"Migración completada. Archivos migrados: {migrated}")


if __name__ == '__main__':
    main()
