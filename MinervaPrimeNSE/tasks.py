import os, json
from filelock import FileLock
from redis import Redis
from MinervaPrimeNSE.Minerva import responder_a_usuario

APP_STATE_DIR = os.getenv("APP_STATE_DIR", "/state")
os.makedirs(APP_STATE_DIR, exist_ok=True)
PREGUNTAS_PATH = os.path.join(APP_STATE_DIR, 'preguntas.json')

def _cargar_preguntas():
    if os.path.exists(PREGUNTAS_PATH):
        with open(PREGUNTAS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _guardar_preguntas(data: dict):
    tmp = PREGUNTAS_PATH + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PREGUNTAS_PATH)

def job_responder(mensaje: str, ia: str, usuario: str, lock_ttl: int = 300) -> dict:
    redis = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
    # Lock distribuido por usuario para serializar peticiones del mismo user
    with redis.lock(f"lock:user:{usuario}", timeout=lock_ttl, blocking_timeout=lock_ttl):
        # Bloqueo de fichero para consistencia al tocar preguntas.json
        with FileLock(PREGUNTAS_PATH + ".lock", timeout=lock_ttl):
            preguntas = _cargar_preguntas()
            # Comentado: validación de tokens eliminada
            # restantes = preguntas.get(usuario, {}).get(ia, 0)
            # if restantes != -1 and restantes <= 0:
            #     return {"respuesta": "⛔ Se acabaron tus preguntas disponibles para esta IA."}
            # if restantes != -1:
            #     preguntas.setdefault(usuario, {}).setdefault(ia, restantes)
            #     preguntas[usuario][ia] -= 1
            #     _guardar_preguntas(preguntas)

        try:
            texto = responder_a_usuario(mensaje, ia, usuario)
            return {"respuesta": texto}
        except Exception as e:
            # Comentado: compensación de tokens eliminada
            # with FileLock(PREGUNTAS_PATH + ".lock", timeout=lock_ttl):
            #     preguntas = _cargar_preguntas()
            #     if preguntas.get(usuario, {}).get(ia) is not None and preguntas[usuario][ia] != -1:
            #         preguntas[usuario][ia] += 1
            #         _guardar_preguntas(preguntas)
            return {"respuesta": f"⚠️ Error procesando la petición: {e}"}
