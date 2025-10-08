import sys
import os
import json
from flask import Flask, request, session, redirect, send_from_directory, jsonify, render_template_string, abort
from datetime import datetime
import bcrypt
import os
from uuid import uuid4
from redis import Redis
from rq import Queue
from rq.job import Job
from MinervaPrimeNSE.tasks import job_responder

app = Flask(__name__)
app.secret_key = 'clave-super-secreta'
REDIS_URL = os.environ["REDIS_URL"]            # ← sin valor por defecto
redis_conn = Redis.from_url(REDIS_URL)         # con redis:// interno no hace falta TLS
queue = Queue("queries", connection=redis_conn, default_timeout=300)

print(f"[RQ] Using Redis URL host: {redis_conn.connection_pool.connection_kwargs.get('host')}", flush=True)

# ========== BASE DE RUTAS Y PERSONAJES ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAJES_PATH = os.path.join(BASE_DIR, 'personajes.json')
PREGUNTAS_PATH = os.path.join(BASE_DIR, 'preguntas.json')

with open(PERSONAJES_PATH, 'r', encoding='utf-8') as f:
    PERSONAJES = json.load(f)

if os.path.exists(PREGUNTAS_PATH):
    with open(PREGUNTAS_PATH, 'r', encoding='utf-8') as f:
        preguntas_restantes = json.load(f)
else:
    preguntas_restantes = {}

# ========== UTILIDADES ==========
def cargar_preguntas():
    global preguntas_restantes
    if os.path.exists(PREGUNTAS_PATH):
        with open(PREGUNTAS_PATH, 'r', encoding='utf-8') as f:
            preguntas_restantes = json.load(f)
    else:
        preguntas_restantes = {}

def guardar_preguntas():
    with open(PREGUNTAS_PATH, 'w', encoding='utf-8') as f:
        json.dump(preguntas_restantes, f, indent=2, ensure_ascii=False)

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
    cargar_preguntas()
    user = request.form.get('usuario', '').strip().lower()
    clave = request.form.get('clave', '').encode('utf-8')
    datos = PERSONAJES.get(user)

    if datos:
        clave_guardada = datos['clave'].encode('utf-8')
        if bcrypt.checkpw(clave, clave_guardada):
            session['usuario'] = user
            session['rol'] = datos.get('rol', 'jugador')

            if user not in preguntas_restantes:
                preguntas_restantes[user] = {
                    "anima": 3,
                    "eidolon": 3,
                    "hada": 3,
                    "fantasma": 3
                }
                guardar_preguntas()

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

        nuevos = request.json
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
        data = request.get_json()
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

from MinervaPrimeNSE.utils import get_name_ia

name_ia = get_name_ia()

@app.route('/<ia>')
def ia_home(ia):
    ia_dir = os.path.join(BASE_DIR, ia)
    return send_from_directory(ia_dir, 'index.html')

@app.route('/<ia>/<path:archivo>')
def ia_static(ia, archivo):
    return send_from_directory(os.path.join(BASE_DIR, ia), archivo)

@app.route('/<ia>/query', methods=['POST'])
def ia_query_ruta(ia):
    data = request.json or {}
    mensaje_original = data.get("mensaje", "")
    usuario = data.get("id", "").strip().lower()
    ia = ia.strip().lower()

    if session.get('usuario', '').lower() != usuario:
        return jsonify({"respuesta": "⚠️ Acceso denegado: sesión inválida."}), 403

    job = queue.enqueue(job_responder, mensaje_original, ia, usuario)
    return jsonify({"job_id": job.get_id()})

@app.route('/query', methods=['POST'])
def ia_query():
    data = request.json or {}
    mensaje_original = data.get("mensaje", "")
    ia = data.get("ia", name_ia).strip().lower()
    usuario = data.get("id", "").strip().lower()

    if session.get('usuario', '').lower() != usuario:
        return jsonify({"respuesta": "⚠️ Acceso denegado: sesión inválida."}), 403

    job = queue.enqueue(job_responder, mensaje_original, ia, usuario)
    return jsonify({"job_id": job.get_id()})

@app.route('/jobs/<job_id>', methods=['GET'])
def job_status(job_id):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        return jsonify({"error": "job no encontrado"}), 404

    if job.is_failed:
        return jsonify({"status": "failed", "error": str(job.exc_info)}), 500
    if job.result is not None:
        # job_responder devuelve {"respuesta": "..."}
        return jsonify({"status": "finished", "result": job.result})
    return jsonify({"status": job.get_status()})


# ========== ADMINISTRACIÓN ==========

def normalizar_personajes(d):
    # Fuerza claves a minúsculas y limpia espacios
    out = {}
    for k, v in d.items():
        out[k.strip().lower()] = v
    return out

# Carga inicial
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

    cargar_preguntas()

    if request.method == 'GET':
        cargar_personajes()  # ✅ Esto garantiza que la vista admin esté siempre actualizada
        lista = []
        for nombre in PERSONAJES.keys():
            user_preguntas = preguntas_restantes.get(nombre, {
                "anima": 0,
                "eidolon": 0,
                "hada": 0,
                "fantasma": 0
            })
            lista.append({
                "nombre": nombre,
                "preguntas": user_preguntas
            })
        return jsonify(lista)

    if request.method == 'POST':
        datos = request.json
        nombre = datos.get('nombre')
        clave = datos.get('clave')
        rol = datos.get('rol', 'jugador')

        if not nombre or not clave:
            return jsonify({"error": "Faltan datos"}), 400

        nombre_lower = nombre.strip().lower()
        clave_hash = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        PERSONAJES[nombre_lower] = {"clave": clave_hash, "rol": rol}
        guardar_personajes()
        cargar_personajes()

        if nombre_lower not in preguntas_restantes:
            preguntas_restantes[nombre_lower] = {
                "anima": 3,
                "eidolon": 3,
                "hada": 3,
                "fantasma": 3
            }

        guardar_preguntas()

        return jsonify({"mensaje": "Personaje creado o actualizado"})

    if request.method == 'DELETE':
        datos = request.json
        nombre = datos.get('nombre')

        if not nombre or nombre.lower() not in PERSONAJES:
            return jsonify({"error": "Personaje no encontrado"}), 404

        nombre_lower = nombre.strip().lower()

        del PERSONAJES[nombre_lower]
        if nombre_lower in preguntas_restantes:
            del preguntas_restantes[nombre_lower]

        guardar_personajes()
        guardar_preguntas()

        return jsonify({"mensaje": "Personaje eliminado"})



    if request.method == 'DELETE':
        datos = request.json
        nombre = datos.get('nombre')

        if not nombre or nombre.lower() not in PERSONAJES:
            return jsonify({"error": "Personaje no encontrado"}), 404

        nombre_lower = nombre.strip().lower()

        del PERSONAJES[nombre_lower]
        if nombre_lower in preguntas_restantes:
            del preguntas_restantes[nombre_lower]

        with open(PERSONAJES_PATH, 'w', encoding='utf-8') as f:
            json.dump(PERSONAJES, f, indent=2, ensure_ascii=False)

        guardar_preguntas()

        return jsonify({"mensaje": "Personaje eliminado"})

@app.route('/admin/personaje/<nombre>')
def obtener_personaje(nombre):
    if session.get('rol') != 'admin':
        return abort(403)

    cargar_preguntas()

    nombre = nombre.strip().lower()
    if nombre not in PERSONAJES:
        return jsonify({"error": "Personaje no encontrado"}), 404

    datos_personaje = PERSONAJES[nombre].copy()
    datos_personaje['preguntas'] = preguntas_restantes.get(nombre, {
        "anima": 0,
        "eidolon": 0,
        "hada": 0,
        "fantasma": 0
    })

    return jsonify(datos_personaje)

@app.route('/admin/resetear-preguntas', methods=['POST'])
def resetear_preguntas():
    if session.get('rol') != 'admin':
        return abort(403)

    datos = request.json
    nombre = datos.get('nombre')

    if not nombre or nombre.lower() not in PERSONAJES:
        return jsonify({"error": "Personaje no encontrado"}), 404

    nombre_lower = nombre.strip().lower()

    preguntas_restantes[nombre_lower] = {
        "anima": 3,
        "eidolon": 3,
        "hada": 3,
        "fantasma": 3
    }
    guardar_preguntas()

    return jsonify({"mensaje": f"Preguntas de {nombre} reseteadas."})

@app.route('/admin/guardar-preguntas', methods=['POST'])
def guardar_preguntas_admin():
    if session.get('rol') != 'admin':
        return abort(403)

    datos = request.json
    cambios = datos.get('cambios', {})

    for nombre, preguntas in cambios.items():
        nombre_lower = nombre.strip().lower()
        if nombre_lower not in preguntas_restantes:
            preguntas_restantes[nombre_lower] = {}
        for ia, valor in preguntas.items():
            preguntas_restantes[nombre_lower][ia] = valor

    guardar_preguntas()

    return jsonify({"mensaje": "Preguntas actualizadas correctamente."})


# ========== NOTAS PERSONALES ==========
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
        datos = request.json
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
    cargar_preguntas()
    usuario = session['usuario'].lower()
    usos = preguntas_restantes.get(usuario, {})
    usos_normalizados = {k.lower(): v for k, v in usos.items()}
    return jsonify(usos_normalizados)

# ========== LOG DE EVENTOS ==========
LOGS_DIR = os.path.join(BASE_DIR, 'admin', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

@app.route('/log-evento', methods=['POST'])
def log_evento():
    if 'usuario' not in session:
        return jsonify({"error": "No autorizado"}), 403

    usuario = session['usuario'].lower()
    datos = request.json
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
    os.makedirs(os.path.dirname(ruta), exist_ok=True)  # Asegura que la carpeta exista

    try:
        nuevo_contenido = request.get_json()
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(nuevo_contenido, f, indent=2, ensure_ascii=False)
        return jsonify({"mensaje": "Ficha creada o actualizada correctamente."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@app.route('/admin/ficha/<nombre>.json', methods=['GET', 'POST'])
def admin_editar_ficha(nombre):
    if session.get('rol') != 'admin':
        return jsonify({"error": "No autorizado"}), 403

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')

    if request.method == 'GET':
        if not os.path.exists(ruta):
            return jsonify({"error": "Ficha no encontrada"}), 404
        with open(ruta, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))

    if request.method == 'POST':
        try:
            datos = request.get_json()
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            return jsonify({"mensaje": "Ficha guardada correctamente."})
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

        nuevos_datos = request.get_json()

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
    app.run(host='0.0.0.0', port=port, debug=port)
