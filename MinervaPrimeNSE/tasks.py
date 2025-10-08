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
        print(f"👤 Usuario {usuario} - Ilimitado: {es_ilimitado}")
        
        # Solo consumir token si es necesario Y el usuario no es ilimitado
        if tipo_consulta["consume_token"] and not es_ilimitado:
            restantes = preguntas.get(usuario, {}).get(ia, 0)
            if restantes != -1 and restantes <= 0:
                return {
                    "respuesta": "⛔ Se acabaron tus preguntas disponibles para esta IA.",
                    "consumio_token": False,
                    "tipo_consulta": tipo_consulta["tipo"],
                    "razon": "Sin tokens disponibles"
                }
            if restantes != -1:
                preguntas.setdefault(usuario, {}).setdefault(ia, restantes)
                preguntas[usuario][ia] -= 1
                _guardar_preguntas(preguntas)
                print(f"💰 Token consumido. Restantes: {preguntas[usuario][ia]}")
        elif es_ilimitado:
            print(f"♾️ Usuario ilimitado - no se consume token")

        try:
            texto = responder_a_usuario(mensaje, ia, usuario)
            
            # Análisis post-respuesta para verificar si realmente se necesitó documentación
            consumo_real = analizar_respuesta_para_consumo(texto, mensaje)
            
            # Si se detectó que no debería haber consumido token, compensar (solo si no es ilimitado)
            if tipo_consulta["consume_token"] and not consumo_real and not es_ilimitado:
                print(f"🔄 Compensando token - respuesta no requirió documentación")
                preguntas = _cargar_preguntas()
                if preguntas.get(usuario, {}).get(ia) is not None and preguntas[usuario][ia] != -1:
                    preguntas[usuario][ia] += 1
                    _guardar_preguntas(preguntas)
                    print(f"💰 Token compensado. Restantes: {preguntas[usuario][ia]}")
            
            return {
                "respuesta": texto,
                "consumio_token": tipo_consulta["consume_token"] and consumo_real and not es_ilimitado,
                "tipo_consulta": tipo_consulta["tipo"],
                "razon": tipo_consulta["razon"]
            }
            
        except Exception as e:
            # Log detallado del error para debugging
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ Error en job_responder: {e}")
            print(f"❌ Traceback: {error_details}")
            
            # Si hubo error y se consumió token, compensar (solo si no es ilimitado)
            if tipo_consulta["consume_token"] and not es_ilimitado:
                preguntas = _cargar_preguntas()
                if preguntas.get(usuario, {}).get(ia) is not None and preguntas[usuario][ia] != -1:
                    preguntas[usuario][ia] += 1
                    _guardar_preguntas(preguntas)
                    print(f"💰 Token compensado por error. Restantes: {preguntas[usuario][ia]}")
            
            return {
                "respuesta": f"⚠️ Error procesando la petición: {e}",
                "consumio_token": False,
                "tipo_consulta": "error",
                "razon": "Error en procesamiento"
            }
