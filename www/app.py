import os
import json
from uuid import uuid4
from datetime import datetime
from urllib.parse import urlparse

import time
from flask import Flask, request, session, redirect, send_from_directory, jsonify, render_template_string, abort
import bcrypt
from redis import Redis
from rq import Queue
from rq.job import Job
from filelock import FileLock  # <<< NUEVO

from MinervaPrimeNSE.tasks import job_responder
from MinervaPrimeNSE.utils import get_name_ia

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "cambia-esto-en-dev")

DEFAULT_QUOTA = int(os.getenv("DEFAULT_QUOTA", "3"))

# ================== REDIS ==================
def build_conn_from_discretes():
    from redis import Redis
    host = os.environ.get("REDISHOST")
    port = int(os.environ.get("REDISPORT", 6379))
    user = os.environ.get("REDISUSER", "default")
    # acepta REDISPASSWORD y REDIS_PASSWORD
    pwd  = os.environ.get("REDISPASSWORD") or os.environ.get("REDIS_PASSWORD")
    app.logger.info(f"[WEB] Using discrete Redis vars host={host} port={port} user={user} pwd_len={len(pwd) if pwd else 0}")
    return Redis(host=host, port=port, username=user, password=pwd)

def build_conn_from_url(url: str) -> Redis:
    """
    Crea una conexión Redis a partir de REDIS_URL.
    Soporta redis:// y rediss:// (TLS).
    """
    app.logger.info(f"[WEB] Using REDIS_URL={url}")
    return Redis.from_url(url)

def get_redis_conn():
    url = (os.environ.get("REDIS_URL") or "").strip()
    # Evita placeholders tipo <PASS>
    if url and "<" not in url and ">" not in url:
        try:
            conn = build_conn_from_url(url)
            conn.ping()
            app.logger.info("[WEB] Redis ping OK via REDIS_URL")
            return conn
        except Exception as e:
            app.logger.exception(f"[WEB] Redis via REDIS_URL FAILED: {e}")

    # Fallback a discretas
    conn = build_conn_from_discretes()
    if conn:
        conn.ping()
        app.logger.info("[WEB] Redis ping OK via discrete vars")
        return conn

    raise RuntimeError("No valid Redis credentials found.")

try:
    redis_conn = get_redis_conn()
except Exception as e:
    app.logger.exception(f"[WEB] Redis init FAILED: {e}")
    redis_conn = None

queue = Queue("queries", connection=redis_conn, default_timeout=600, job_timeout=600) if redis_conn else None

# ========== BASE DE RUTAS Y PERSONAJES ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAJES_PATH = os.path.join(BASE_DIR, 'personajes.json')

# >>> Usa la MISMA ruta que el worker
APP_STATE_DIR = os.getenv("APP_STATE_DIR", "/state")
os.makedirs(APP_STATE_DIR, exist_ok=True)
PREGUNTAS_PATH = os.path.join(APP_STATE_DIR, 'preguntas.json')

with open(PERSONAJES_PATH, 'r', encoding='utf-8') as f:
    PERSONAJES = json.load(f)

# ========== HELPERS DE PREGUNTAS (con lock, sin cache global) ==========
def _cargar_preguntas() -> dict:
    if os.path.exists(PREGUNTAS_PATH):
        with open(PREGUNTAS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _guardar_preguntas(data: dict):
    tmp = PREGUNTAS_PATH + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PREGUNTAS_PATH)

def _with_preguntas_locked(mutator=None, timeout=10):
    """
    Lee preguntas con lock, aplica mutator(data)->(changed,data) opcional,
    guarda si cambió y devuelve data final.
    """
    lock = FileLock(PREGUNTAS_PATH + ".lock", timeout=timeout)
    with lock:
        data = _cargar_preguntas()
        if mutator is not None:
            changed, data = mutator(data)
            if changed:
                _guardar_preguntas(data)
        return data

def is_unlimited_user(username: str) -> bool:
    u = (username or "").strip().lower()
    info = PERSONAJES.get(u, {})
    # Todos los usuarios son ilimitados
    return True

def ensure_unlimited_seed(user: str):
    """
    Si el usuario es ilimitado y su semilla no está a -1, la normaliza a -1 para todas las IAs.
    """
    def _mut(data):
        changed = False
        u = (user or "").strip().lower()
        if not u:
            return False, data
        cur = data.get(u) or {}
        # normaliza TODAS las claves presentes, y si faltan crea las conocidas
        ias = set(cur.keys()) | {"anima", "eidolon", "hada", "fantasma", "minerva"}
        for ia in ias:
            if cur.get(ia) != -1:
                cur[ia] = -1
                changed = True
        data[u] = cur
        return changed, data
    _with_preguntas_locked(_mut)

# ========== MIGRACIÓN LEGACY (si el fichero estaba en BASE_DIR) ==========
LEGACY_PREG_PATH = os.path.join(BASE_DIR, 'preguntas.json')
try:
    if not os.path.exists(PREGUNTAS_PATH) and os.path.exists(LEGACY_PREG_PATH):
        # Asegurar que el directorio existe
        os.makedirs(APP_STATE_DIR, exist_ok=True)
        
        with open(LEGACY_PREG_PATH, 'r', encoding='utf-8') as f:
            legacy = json.load(f)
        
        # normaliza claves a lower case
        migrated = { (k or '').strip().lower(): v for k, v in legacy.items() }
        
        # Crear archivo temporal con manejo de errores
        tmp = PREGUNTAS_PATH + ".tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(migrated, f, ensure_ascii=False, indent=2)
            
            # Verificar que el archivo temporal se creó correctamente
            if os.path.exists(tmp):
                os.replace(tmp, PREGUNTAS_PATH)
                app.logger.warning(f"[USOS] Migrated preguntas.json from {LEGACY_PREG_PATH} -> {PREGUNTAS_PATH}")
            else:
                app.logger.error(f"[USOS] Failed to create temporary file: {tmp}")
                
        except Exception as tmp_error:
            app.logger.error(f"[USOS] Failed to create temporary file: {tmp_error}")
            # Limpiar archivo temporal si existe
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except:
                    pass
                    
except Exception as e:
    app.logger.exception(f"[USOS] Migration failed: {e}")

# ========== UTILIDADES VARIAS ==========
def obtener_nombre_objetivo():
    if session.get('usuario') == 'narrador':
        return request.args.get('id')
    return session.get('usuario')

# ========== MIDDLEWARE DE SESIÓN ==========
@app.before_request
def validar_sesion():
    rutas_publicas = ['/', '/login', '/logout', '/favicon.ico', '/session-info', '/usos']
    if (
        any(request.path.startswith(ruta) for ruta in rutas_publicas)
        or request.path.endswith(('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot'))
        or request.path.startswith('/static')
    ):
        return
    if 'usuario' not in session:
        return redirect('/')

# ========== LOGIN Y LOGOUT ==========
@app.route('/')
def login():
    error = request.args.get('error')
    login_path = os.path.join(BASE_DIR, 'login', 'index.html')
    with open(login_path, 'r', encoding='utf-8') as f:
        template = f.read()
    return render_template_string(template, error=error)

@app.route('/login', methods=['POST'])
def do_login():
    user = request.form.get('usuario', '').strip().lower()
    clave = request.form.get('clave', '').encode('utf-8')
    datos = PERSONAJES.get(user)

    if datos:
        clave_guardada = datos['clave'].encode('utf-8')
        if bcrypt.checkpw(clave, clave_guardada):
            session['usuario'] = user
            session['rol'] = datos.get('rol', 'jugador')

            # Inicializa preguntas del usuario si no existen (con lock) respetando plan
            if is_unlimited_user(user):
                ensure_unlimited_seed(user)
            else:
                def init_preguntas_if_needed(data):
                    changed = False
                    if user not in data:
                        data[user] = {
                            "anima": DEFAULT_QUOTA,
                            "eidolon": DEFAULT_QUOTA,
                            "hada": DEFAULT_QUOTA,
                            "fantasma": DEFAULT_QUOTA,
                            "minerva": 0
                        }
                        changed = True
                    return changed, data
                _with_preguntas_locked(init_preguntas_if_needed)

            return redirect('/panel' if user == 'narrador' else '/ficha')

    return redirect('/?error=Credenciales incorrectas')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/session-info')
def session_info():
    return jsonify({
        "usuario": session.get("usuario", None),
        "rol": session.get("rol", None)
    })

# ========== FICHA ==========
@app.route('/ficha')
def acceder_ficha():
    path = os.path.join(BASE_DIR, 'ficha')
    return send_from_directory(path, 'index.html')

@app.route('/ficha/personaje.json')
def obtener_json_seguro():
    nombre = obtener_nombre_objetivo()
    if not nombre:
        return jsonify({"error": "Falta parámetro 'id'"}), 400

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    if not os.path.exists(ruta):
        return jsonify({"error": "No encontrado"}), 404

    with open(ruta, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {session['usuario']} accede a ficha de {nombre}", flush=True)
    return jsonify(datos)

@app.route('/ficha/personajes/personaje.json')
def obtener_ficha_personaje():
    nombre = session.get('usuario', '').strip().lower()
    if not nombre:
        return jsonify({"error": "Usuario no autenticado"}), 403

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    if not os.path.exists(ruta):
        return jsonify({"error": "Ficha no encontrada"}), 404

    with open(ruta, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route("/ficha/guardar", methods=["POST"])
def guardar_ficha():
    try:
        nombre = session.get('usuario', '').strip().lower()
        if not nombre:
            return jsonify({"error": "Usuario no autenticado"}), 403

        path = os.path.join(BASE_DIR, "ficha", "personajes", f"{nombre}.json")
        if not os.path.exists(path):
            return jsonify({"error": "Archivo no encontrado"}), 404

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        nuevos = request.get_json(silent=True) or {}
        data.update(nuevos)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return jsonify({"mensaje": "Guardado con éxito."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== CONEXIONES ==========
@app.route('/conexiones')
def ver_conexiones():
    path = os.path.join(BASE_DIR, 'conexiones')
    return send_from_directory(path, 'index.html')

@app.route('/conexiones/<path:archivo>')
def static_conexiones(archivo):
    path = os.path.join(BASE_DIR, 'conexiones')
    return send_from_directory(path, archivo)

@app.route('/conexiones/personajes/<nombre>.json', methods=['GET', 'POST'])
def manejar_conexiones(nombre):
    ruta = os.path.join(BASE_DIR, 'conexiones', 'personajes', f'{nombre}.json')

    if request.method == 'GET':
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        else:
            return jsonify({"elements": {"nodes": [], "edges": []}}), 404

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        if not data:
            return jsonify({"error": "No se recibió data válida."}), 400

        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return jsonify({"mensaje": f"Archivo {nombre}.json guardado correctamente."})

# ========== PANEL ==========
@app.route('/panel')
def panel():
    if session.get('usuario') != 'narrador':
        return redirect('/')
    path = os.path.join(BASE_DIR, 'narrador')
    return send_from_directory(path, 'index.html')

name_ia = get_name_ia()

@app.route('/<ia>')
def ia_home(ia):
    ia_dir = os.path.join(BASE_DIR, ia)
    return send_from_directory(ia_dir, 'index.html')

@app.route('/<ia>/<path:archivo>')
def ia_static(ia, archivo):
    return send_from_directory(os.path.join(BASE_DIR, ia), archivo)

# ========== CONSULTAS (cola RQ) ==========
def _wrap_ok(payload: dict, ia: str, usuario: str, job_id: str):
    # payload viene del worker: {"respuesta": "..."} o {"respuesta":"⛔ ..."}
    resp_text = None
    if isinstance(payload, dict):
        resp_text = payload.get("respuesta")
    elif isinstance(payload, str):
        resp_text = payload
        payload = {"respuesta": resp_text}
    else:
        payload = {"respuesta": str(payload)}
        resp_text = str(payload["respuesta"])

    # Envoltura compatible
    wrapped = {
        "ok": True,
        "respuesta": resp_text,
        "answer": resp_text,     # alias por si el front mira 'answer'
        "ia": ia,
        "id": usuario,
        "job_id": job_id
    }
    # conserva el resto del payload original
    for k, v in payload.items():
        if k not in wrapped:
            wrapped[k] = v
    return wrapped

def _wrap_err(msg: str, ia: str, usuario: str, job_id: str = None, status: str = None):
    return {
        "ok": False,
        "error": msg,
        "ia": ia,
        "id": usuario,
        "job_id": job_id,
        "status": status
    }

def _enqueue_and_wait(mensaje: str, ia: str, usuario: str, wait_timeout: int = 60, poll_interval: float = 0.25):
    job = queue.enqueue(job_responder, mensaje, ia, usuario, job_timeout=600, result_ttl=1200)

    deadline = time.time() + wait_timeout
    last_status = None

    while time.time() < deadline:
        try:
            status = job.get_status(refresh=True)
            last_status = status

            if status == "finished" and job.result is not None:
                wrapped = _wrap_ok(job.result, ia, usuario, job.get_id())
                return 200, wrapped

            if status == "failed":
                error_msg = "Servicio temporalmente no disponible"
                if hasattr(job, 'exc_info') and job.exc_info:
                    error_msg = f"Error en procesamiento: {str(job.exc_info)}"
                return 200, _wrap_err(error_msg, ia, usuario, job.get_id(), "failed")

            # Log del estado para debugging
            app.logger.info(f"[QUEUE] Job {job.get_id()} status: {status}")
            
        except Exception as e:
            app.logger.error(f"[QUEUE] Error checking job status: {e}")
            return 200, _wrap_err(f"Error de comunicación con worker: {str(e)}", ia, usuario, job.get_id(), "error")

        time.sleep(poll_interval)

    # 202 → respondemos 200 con ok:false para que el front SIEMPRE pinte algo
    return 200, _wrap_err("Procesando… vuelve a intentarlo", ia, usuario, job.get_id(), (last_status or "queued"))


@app.route('/<ia>/query', methods=['POST'])
def ia_query_ruta(ia):
    data = request.get_json(silent=True) or {}
    mensaje_original = data.get("mensaje", "")
    usuario = (data.get("id") or "").strip().lower()
    ia = ia.strip().lower()

    if not usuario:
        return jsonify({"error": "Falta id"}), 400
    if (session.get('usuario') or '').lower() != usuario:
        return jsonify({"respuesta": "⚠️ Acceso denegado: sesión inválida."}), 403
    if not queue:
        return jsonify({"error": "Servicio de colas no disponible"}), 503

    # autocuramos ilimitado antes de encolar
    if is_unlimited_user(usuario):
        ensure_unlimited_seed(usuario)

    status_code, payload = _enqueue_and_wait(mensaje_original, ia, usuario, wait_timeout=60, poll_interval=0.25)
    app.logger.info(f"[QUERY] ia={ia} user={usuario} ok={payload.get('ok')} has_respuesta={bool(payload.get('respuesta'))} len={len((payload.get('respuesta') or ''))}")
    return jsonify(payload), status_code

@app.route('/query', methods=['POST'])
def ia_query():
    data = request.get_json(silent=True) or {}
    mensaje_original = data.get("mensaje", "")
    ia = (data.get("ia") or name_ia).strip().lower()
    usuario = (data.get("id") or "").strip().lower()

    if not usuario:
        return jsonify({"error": "Falta id"}), 400
    if (session.get('usuario') or '').lower() != usuario:
        return jsonify({"respuesta": "⚠️ Acceso denegado: sesión inválida."}), 403
    if not queue:
        return jsonify({"error": "Servicio de colas no disponible"}), 503

    # autocuramos ilimitado antes de encolar
    if is_unlimited_user(usuario):
        ensure_unlimited_seed(usuario)

    status_code, payload = _enqueue_and_wait(mensaje_original, ia, usuario, wait_timeout=60, poll_interval=0.25)
    app.logger.info(f"[QUERY] ia={ia} user={usuario} ok={payload.get('ok')} has_respuesta={bool(payload.get('respuesta'))} len={len((payload.get('respuesta') or ''))}")
    return jsonify(payload), status_code

@app.route('/jobs/<job_id>', methods=['GET'])
def job_status(job_id):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return jsonify({"error": "job no encontrado"}), 404

    if job.is_failed:
        return jsonify({"status": "failed", "error": str(job.exc_info)}), 500
    if job.result is not None:
        return jsonify({"status": "finished", "result": job.result})
    return jsonify({"status": job.get_status()})

# ========== ADMINISTRACIÓN ==========
def normalizar_personajes(d):
    out = {}
    for k, v in d.items():
        out[k.strip().lower()] = v
    return out

with open(PERSONAJES_PATH, 'r', encoding='utf-8') as f:
    PERSONAJES = normalizar_personajes(json.load(f))

def cargar_personajes():
    global PERSONAJES
    with open(PERSONAJES_PATH, 'r', encoding='utf-8') as f:
        PERSONAJES = normalizar_personajes(json.load(f))

def guardar_personajes():
    with open(PERSONAJES_PATH, 'w', encoding='utf-8') as f:
        json.dump(PERSONAJES, f, indent=2, ensure_ascii=False)

@app.route('/admin')
def admin_panel():
    if session.get('rol') != 'admin':
        abort(403)
    path = os.path.join(BASE_DIR, 'admin')
    return send_from_directory(path, 'index.html')

@app.route('/admin/personajes', methods=['GET', 'POST', 'DELETE'])
def admin_personajes():
    if session.get('rol') != 'admin':
        return abort(403)

    if request.method == 'GET':
        cargar_personajes()
        data = _with_preguntas_locked(lambda d: (False, d))
        lista = []
        for nombre in PERSONAJES.keys():
            user_preguntas = data.get(nombre, {
                "anima": 0, "eidolon": 0, "hada": 0, "fantasma": 0, "minerva": 0
            })
            lista.append({"nombre": nombre, "preguntas": user_preguntas})
        return jsonify(lista)

    if request.method == 'POST':
        datos = request.get_json(silent=True) or {}
        nombre = datos.get('nombre')
        clave = datos.get('clave')
        rol = datos.get('rol', 'jugador')
        plan = datos.get('plan')  # opcional

        if not nombre or not clave:
            return jsonify({"error": "Faltan datos"}), 400

        nombre_lower = nombre.strip().lower()
        clave_hash = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        PERSONAJES[nombre_lower] = {"clave": clave_hash, "rol": rol}
        if plan:
            PERSONAJES[nombre_lower]["plan"] = plan
        guardar_personajes()
        cargar_personajes()

        # siembra respetando plan
        if is_unlimited_user(nombre_lower):
            ensure_unlimited_seed(nombre_lower)
        else:
            def upsert_pregs(data):
                changed = False
                if nombre_lower not in data:
                    data[nombre_lower] = {"anima": DEFAULT_QUOTA, "eidolon": DEFAULT_QUOTA, "hada": DEFAULT_QUOTA, "fantasma": DEFAULT_QUOTA, "minerva": 0}
                    changed = True
                return changed, data
            _with_preguntas_locked(upsert_pregs)

        return jsonify({"mensaje": "Personaje creado o actualizado"})

    if request.method == 'DELETE':
        datos = request.get_json(silent=True) or {}
        nombre = datos.get('nombre')

        if not nombre or nombre.lower() not in PERSONAJES:
            return jsonify({"error": "Personaje no encontrado"}), 404

        nombre_lower = nombre.strip().lower()
        del PERSONAJES[nombre_lower]
        guardar_personajes()

        def remove_user(data):
            changed = False
            if nombre_lower in data:
                del data[nombre_lower]
                changed = True
            return changed, data
        _with_preguntas_locked(remove_user)

        return jsonify({"mensaje": "Personaje eliminado"})

@app.route('/admin/personaje/<nombre>')
def obtener_personaje(nombre):
    if session.get('rol') != 'admin':
        return abort(403)

    nombre = nombre.strip().lower()
    if nombre not in PERSONAJES:
        return jsonify({"error": "Personaje no encontrado"}), 404

    data = _with_preguntas_locked(lambda d: (False, d))
    datos_personaje = PERSONAJES[nombre].copy()
    datos_personaje['preguntas'] = data.get(nombre, {"anima": 0, "eidolon": 0, "hada": 0, "fantasma": 0, "minerva": 0})
    return jsonify(datos_personaje)

@app.route('/admin/resetear-preguntas', methods=['POST'])
def resetear_preguntas():
    if session.get('rol') != 'admin':
        return abort(403)

    datos = request.get_json(silent=True) or {}
    nombre = datos.get('nombre')

    if not nombre or nombre.lower() not in PERSONAJES:
        return jsonify({"error": "Personaje no encontrado"}), 404

    nombre_lower = nombre.strip().lower()

    if is_unlimited_user(nombre_lower):
        ensure_unlimited_seed(nombre_lower)
    else:
        def reset_user(data):
            data[nombre_lower] = {"anima": DEFAULT_QUOTA, "eidolon": DEFAULT_QUOTA, "hada": DEFAULT_QUOTA, "fantasma": DEFAULT_QUOTA, "minerva": 0}
            return True, data
        _with_preguntas_locked(reset_user)

    return jsonify({"mensaje": f"Preguntas de {nombre} reseteadas."})

@app.route('/admin/guardar-preguntas', methods=['POST'])
def guardar_preguntas_admin():
    if session.get('rol') != 'admin':
        return abort(403)

    datos = request.get_json(silent=True) or {}
    cambios = datos.get('cambios', {})

    def apply_changes(data):
        changed = False
        for nombre, preguntas in cambios.items():
            nombre_lower = nombre.strip().lower()
            if is_unlimited_user(nombre_lower):
                # para ilimitados, fuerzo -1
                cur = data.get(nombre_lower, {})
                for ia in set(cur.keys()) | set(preguntas.keys()) | {"anima", "eidolon", "hada", "fantasma", "minerva"}:
                    if cur.get(ia) != -1:
                        cur[ia] = -1
                        changed = True
                data[nombre_lower] = cur
                continue
            if nombre_lower not in data:
                data[nombre_lower] = {}
                changed = True
            for ia, valor in preguntas.items():
                data[nombre_lower][ia] = int(valor)
                changed = True
        return changed, data

    _with_preguntas_locked(apply_changes)
    return jsonify({"mensaje": "Preguntas actualizadas correctamente."})

# ========== HISTORIAL ==========
@app.route("/historial/<ia>/<usuario>")
def obtener_historial(ia, usuario):
    """Obtiene el historial de conversación de un usuario con una IA específica."""
    try:
        historial_dir = os.path.join(BASE_DIR, "historiales")
        historial_path = os.path.join(historial_dir, f"{usuario}_{ia.lower()}_historial.json")
        
        if os.path.exists(historial_path):
            with open(historial_path, "r", encoding="utf-8") as f:
                historial = json.load(f)
            return jsonify({"historial": historial})
        else:
            return jsonify({"historial": []})
    except Exception as e:
        app.logger.error(f"Error obteniendo historial: {e}")
        return jsonify({"historial": []}), 500

@app.route("/admin/limpiar-cache", methods=['POST'])
def limpiar_cache():
    """Limpia el caché de datos para forzar recarga de archivos TXT."""
    if session.get('rol') != 'admin':
        return abort(403)
    
    try:
        from MinervaPrimeNSE.Minerva import limpiar_cache
        limpiar_cache()
        return jsonify({"mensaje": "✅ Caché limpiado exitosamente"})
    except Exception as e:
        app.logger.error(f"Error limpiando caché: {e}")
        return jsonify({"error": f"Error limpiando caché: {e}"}), 500

# ========== NOTAS ==========
@app.route('/notas')
def ver_notas():
    if 'usuario' not in session:
        return redirect('/')
    path = os.path.join(BASE_DIR, 'notas')
    return send_from_directory(path, 'index.html')

@app.route('/notas/contenido', methods=['GET', 'POST'])
def gestionar_notas():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 403

    usuario = session['usuario'].lower()
    ruta_nota = os.path.join(BASE_DIR, 'notas', 'usuarios', f'{usuario}.txt')

    if request.method == 'GET':
        if os.path.exists(ruta_nota):
            with open(ruta_nota, 'r', encoding='utf-8') as f:
                contenido = f.read()
            return jsonify({"contenido": contenido})
        else:
            return jsonify({"contenido": ""})

    if request.method == 'POST':
        datos = request.get_json(silent=True) or {}
        contenido = datos.get('contenido', '')

        os.makedirs(os.path.dirname(ruta_nota), exist_ok=True)
        with open(ruta_nota, 'w', encoding='utf-8') as f:
            f.write(contenido)

        return jsonify({"mensaje": "Notas guardadas correctamente."})

# ========== USOS ==========
@app.route('/usos')
def usos_actuales():
    if 'usuario' not in session:
        return jsonify({})
    usuario = (session['usuario'] or '').strip().lower()

    # autocura: si es ilimitado, fuerza -1 en el fichero
    if is_unlimited_user(usuario):
        ensure_unlimited_seed(usuario)

    data = _with_preguntas_locked(lambda d: (False, d))
    usos = data.get(usuario, {})

    # LOG útil para depurar qué se está sirviendo y desde dónde
    app.logger.info(f"[USOS] path={PREGUNTAS_PATH} user={usuario} payload={usos}")

    # Si quisieras evitar -1 en el front, podrías mapear aquí a 999999:
    # NORMALIZED_INFINITY = 999999
    # usos = {k: (NORMALIZED_INFINITY if v == -1 else v) for k, v in usos.items()}

    return jsonify({k.lower(): v for k, v in usos.items()})

# ========== LOGS ==========
LOGS_DIR = os.path.join(BASE_DIR, 'admin', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

@app.route('/log-evento', methods=['POST'])
def log_evento():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 403

    usuario = session['usuario'].lower()
    datos = request.get_json(silent=True) or {}
    tipo = datos.get('tipo')
    contenido = datos.get('contenido')

    if not tipo or not contenido:
        return jsonify({"error": "Faltan datos"}), 400

    evento = {
        "timestamp": datetime.now().isoformat(),
        "tipo": tipo,
        "contenido": contenido
    }

    ruta_log = os.path.join(LOGS_DIR, f"{usuario}.json")

    if os.path.exists(ruta_log):
        try:
            with open(ruta_log, 'r', encoding='utf-8') as f:
                eventos = json.load(f)
        except Exception:
            eventos = []
    else:
        eventos = []

    eventos.append(evento)

    with open(ruta_log, 'w', encoding='utf-8') as f:
        json.dump(eventos, f, indent=2, ensure_ascii=False)

    return jsonify({"mensaje": "Evento registrado"})

@app.route('/admin/logs/<nombre>.json', methods=['DELETE'])
def borrar_log_personaje(nombre):
    if session.get('rol') != 'admin':
        return jsonify({"error": "No autorizado"}), 403

    ruta_log = os.path.join(LOGS_DIR, f"{nombre}.json")

    try:
        if os.path.exists(ruta_log):
            os.remove(ruta_log)
            return jsonify({"mensaje": "Log eliminado correctamente."})
        else:
            return jsonify({"mensaje": "No hay log que eliminar."})
    except Exception as e:
        return jsonify({"error": f"Error al borrar el log: {str(e)}"}), 500

# ========== FICHA (ADMIN) ==========
@app.route('/admin/ficha/<nombre>.json', methods=['GET'])
def admin_obtener_ficha_json(nombre):
    if session.get('rol') != 'admin':
        return jsonify({"error": "No autorizado"}), 403

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    if not os.path.exists(ruta):
        return jsonify({"error": "Ficha no encontrada"}), 404

    with open(ruta, 'r', encoding='utf-8') as f:
        return jsonify(json.load(f))

@app.route('/admin/ficha/<nombre>.json', methods=['POST'])
def admin_guardar_ficha_json(nombre):
    if session.get('rol') != 'admin':
        return jsonify({"error": "No autorizado"}), 403

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    try:
        nuevo_contenido = request.get_json(silent=True) or {}
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(nuevo_contenido, f, indent=2, ensure_ascii=False)
        return jsonify({"mensaje": "Ficha creada o actualizada correctamente."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/ficha/<nombre>.json', methods=['PATCH'])
def admin_actualizar_ficha_parcial(nombre):
    if session.get('rol') != 'admin':
        return jsonify({"error": "No autorizado"}), 403

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    if not os.path.exists(ruta):
        return jsonify({"error": "Ficha no encontrada"}), 404

    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            datos_actuales = json.load(f)

        nuevos_datos = request.get_json(silent=True) or {}

        def actualizar_recursivo(destino, fuente):
            for clave, valor in fuente.items():
                if isinstance(valor, dict) and clave in destino and isinstance(destino[clave], dict):
                    actualizar_recursivo(destino[clave], valor)
                else:
                    destino[clave] = valor

        actualizar_recursivo(datos_actuales, nuevos_datos)

        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(datos_actuales, f, ensure_ascii=False, indent=2)

        return jsonify({"mensaje": "Campo actualizado correctamente."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== RUN ==========
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG') == '1'
    app.run(host='0.0.0.0', port=port, debug=debug)
