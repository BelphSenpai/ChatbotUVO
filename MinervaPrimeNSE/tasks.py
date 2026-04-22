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

def job_responder(mensaje: str, ia: str, usuario: str, lock_ttl: int = 10) -> dict:
    redis = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
    ia_normalizada = (ia or "").strip().lower()
    
    # Importar funciones de detección
    from MinervaPrimeNSE.Minerva import detectar_tipo_consulta, analizar_respuesta_para_consumo
    
    # Detectar tipo de consulta ANTES de procesar
    tipo_consulta = detectar_tipo_consulta(mensaje)
    print(f"🔍 Detección: {tipo_consulta['tipo']} - {tipo_consulta['razon']} - Consume token: {tipo_consulta['consume_token']}")
    
    # Lock distribuido por usuario para serializar peticiones del mismo user
    with redis.lock(f"lock:user:{usuario}", timeout=lock_ttl, blocking_timeout=lock_ttl):
        preguntas = _cargar_preguntas()
        
        # Verificar si el usuario es ilimitado ANTES de verificar tokens
        from www.app import is_unlimited_user
        es_ilimitado = is_unlimited_user(usuario)
        es_ia_gratuita = ia_normalizada == "yggdrassil"
        print(f"👤 Usuario {usuario} - Ilimitado: {es_ilimitado}")
        
        # Si es ilimitado, procesar directamente sin verificar tokens
        if es_ilimitado or es_ia_gratuita:
            if es_ilimitado:
                print(f"♾️ Usuario ilimitado - procesando sin restricciones")
            else:
                print(f"🆓 IA gratuita ({ia_normalizada}) - procesando sin consumir tokens")
            try:
                texto = responder_a_usuario(mensaje, ia, usuario)
                return {
                    "respuesta": texto,
                    "consumio_token": False,
                    "tipo_consulta": tipo_consulta["tipo"],
                    "razon": "Usuario ilimitado" if es_ilimitado else "IA gratuita"
                }
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"❌ Error en job_responder: {e}")
                print(f"❌ Traceback: {error_details}")
                return {
                    "respuesta": f"⚠️ Error procesando la petición: {e}",
                    "consumio_token": False,
                    "tipo_consulta": "error",
                    "razon": "Error en procesamiento"
                }

        # Para usuarios limitados, procesar primero y luego verificar consumo (fuente: Redis)
        try:
            texto = responder_a_usuario(mensaje, ia, usuario)
            
            # Análisis post-respuesta para verificar si realmente se necesitó documentación
            consumo_real = analizar_respuesta_para_consumo(texto, mensaje)
            
            # Solo verificar tokens si realmente se necesita consumir
            if tipo_consulta["consume_token"] and consumo_real:
                user_key = (usuario or "").strip().lower()
                ia_key = (ia or "").strip().lower()
                cur = redis.hget(f"tokens:{user_key}", ia_key)
                cur = int(cur) if cur is not None else 0
                if cur != -1 and cur <= 0:
                    return {
                        "respuesta": "⛔ Se acabaron tus preguntas disponibles para esta IA.",
                        "consumio_token": False,
                        "tipo_consulta": tipo_consulta["tipo"],
                        "razon": "Sin tokens disponibles"
                    }
                if cur != -1:
                    nuevo = max(0, cur - 1)
                    redis.hset(f"tokens:{user_key}", ia_key, nuevo)
                    print(f"💰 Token consumido. Restantes: {nuevo}")
            
            return {
                "respuesta": texto,
                "consumio_token": tipo_consulta["consume_token"] and consumo_real,
                "tipo_consulta": tipo_consulta["tipo"],
                "razon": tipo_consulta["razon"]
            }
            
        except Exception as e:
            # Log detallado del error para debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error en job_responder: {e}")
            print(f"❌ Traceback: {error_details}")
            
            return {
                "respuesta": f"⚠️ Error procesando la petición: {e}",
                "consumio_token": False,
                "tipo_consulta": "error",
                "razon": "Error en procesamiento"
            }
