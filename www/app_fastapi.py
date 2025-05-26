import sys
import os
import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import bcrypt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IA_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'MinervaPrimeSE'))
if IA_DIR not in sys.path:
    sys.path.insert(0, IA_DIR)

from utils import get_name_ia
from Minerva import responder_a_usuario

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAJES_PATH = os.path.join(BASE_DIR, 'personajes.json')
PREGUNTAS_PATH = os.path.join(BASE_DIR, 'preguntas.json')
LOGS_DIR = os.path.join(BASE_DIR, 'admin', 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

with open(PERSONAJES_PATH, 'r', encoding='utf-8') as f:
    PERSONAJES = json.load(f)

if os.path.exists(PREGUNTAS_PATH):
    with open(PREGUNTAS_PATH, 'r', encoding='utf-8') as f:
        preguntas_restantes = json.load(f)
else:
    preguntas_restantes = {}

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="clave-super-secreta")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

name_ia = get_name_ia()

# UTILIDADES

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

def obtener_nombre_objetivo(request: Request):
    if request.session.get('usuario') == 'narrador':
        return request.query_params.get('id')
    return request.session.get('usuario')

# SESIÓN Y LOGIN

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    error = request.query_params.get("error", "")
    login_path = os.path.join(BASE_DIR, 'login', 'index.html')
    with open(login_path, 'r', encoding='utf-8') as f:
        template = f.read()
    return HTMLResponse(template.replace("{{ error }}", error))

@app.post("/login")
async def do_login(request: Request, usuario: str = Form(...), clave: str = Form(...)):
    cargar_preguntas()
    user = usuario.strip().lower()
    clave = clave.encode('utf-8')
    datos = PERSONAJES.get(user)

    if datos:
        clave_guardada = datos['clave'].encode('utf-8')
        if bcrypt.checkpw(clave, clave_guardada):
            request.session['usuario'] = user
            request.session['rol'] = datos.get('rol', 'jugador')

            if user not in preguntas_restantes:
                preguntas_restantes[user] = {"anima": 3, "eidolon": 3, "hada": 3, "fantasma": 3}
                guardar_preguntas()

            destino = '/panel' if user == 'narrador' else '/ficha'
            return RedirectResponse(url=destino, status_code=302)

    return RedirectResponse(url='/?error=Credenciales%20incorrectas', status_code=302)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)

@app.get("/session-info")
async def session_info(request: Request):
    return JSONResponse({"usuario": request.session.get("usuario"), "rol": request.session.get("rol")})

# FICHA

@app.get("/ficha")
async def acceder_ficha():
    return FileResponse(os.path.join(BASE_DIR, 'ficha', 'index.html'))

@app.get("/ficha/personaje.json")
async def obtener_json_seguro(request: Request):
    nombre = obtener_nombre_objetivo(request)
    if not nombre:
        raise HTTPException(status_code=400, detail="Falta parámetro 'id'")

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="No encontrado")

    with open(ruta, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {request.session['usuario']} accede a ficha de {nombre}", flush=True)
    return JSONResponse(datos)

@app.get("/ficha/personajes/personaje.json")
async def obtener_ficha_personaje(request: Request):
    nombre = request.session.get('usuario', '').strip().lower()
    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Ficha no encontrada")
    with open(ruta, 'r', encoding='utf-8') as f:
        return JSONResponse(json.load(f))

@app.post("/ficha/guardar")
async def guardar_ficha(request: Request):
    nombre = request.session.get('usuario', '').strip().lower()
    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')

    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    nuevos = await request.json()
    with open(ruta, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data.update(nuevos)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return JSONResponse({"mensaje": "Guardado con éxito."})

# IA (consulta principal)

@app.post("/query")
async def ia_query(request: Request):
    cargar_preguntas()
    data = await request.json()
    mensaje_original = data.get("mensaje", "")
    ia = data.get("ia", name_ia).strip().lower()
    usuario = data.get("id", "").strip().lower()

    if request.session.get('usuario', '').lower() != usuario:
        raise HTTPException(status_code=403, detail="⚠️ Acceso denegado: sesión inválida.")

    restantes = preguntas_restantes.get(usuario, {}).get(ia, 0)
    if restantes != -1 and restantes <= 0:
        return JSONResponse({"respuesta": "⛔ Se acabaron tus preguntas disponibles para esta IA."})

    respuesta = responder_a_usuario(mensaje_original, ia, usuario)
    if restantes != -1:
        preguntas_restantes[usuario][ia] -= 1
        guardar_preguntas()
    return JSONResponse({"respuesta": respuesta})

[...] # El código anterior permanece igual hasta el final del endpoint /query

# ADMINISTRACIÓN

@app.get("/admin")
async def admin_panel(request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)
    return FileResponse(os.path.join(BASE_DIR, 'admin', 'index.html'))

@app.route("/admin/personajes", methods=["GET", "POST", "DELETE"])
async def admin_personajes(request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)

    cargar_preguntas()
    if request.method == "GET":
        lista = []
        for nombre in PERSONAJES:
            user_preguntas = preguntas_restantes.get(nombre, {"anima": 0, "eidolon": 0, "hada": 0, "fantasma": 0})
            lista.append({"nombre": nombre, "preguntas": user_preguntas})
        return JSONResponse(lista)

    data = await request.json()
    if request.method == "POST":
        nombre = data.get("nombre")
        clave = data.get("clave")
        rol = data.get("rol", "jugador")
        if not nombre or not clave:
            raise HTTPException(status_code=400, detail="Faltan datos")

        nombre_lower = nombre.strip().lower()
        clave_hash = bcrypt.hashpw(clave.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        PERSONAJES[nombre_lower] = {"clave": clave_hash, "rol": rol}

        if nombre_lower not in preguntas_restantes:
            preguntas_restantes[nombre_lower] = {"anima": 3, "eidolon": 3, "hada": 3, "fantasma": 3}

        with open(PERSONAJES_PATH, 'w', encoding='utf-8') as f:
            json.dump(PERSONAJES, f, indent=2, ensure_ascii=False)
        guardar_preguntas()
        return JSONResponse({"mensaje": "Personaje creado o actualizado"})

    if request.method == "DELETE":
        nombre = data.get("nombre")
        if not nombre or nombre.lower() not in PERSONAJES:
            raise HTTPException(status_code=404, detail="Personaje no encontrado")

        nombre_lower = nombre.strip().lower()
        del PERSONAJES[nombre_lower]
        preguntas_restantes.pop(nombre_lower, None)

        with open(PERSONAJES_PATH, 'w', encoding='utf-8') as f:
            json.dump(PERSONAJES, f, indent=2, ensure_ascii=False)
        guardar_preguntas()
        return JSONResponse({"mensaje": "Personaje eliminado"})

@app.get("/admin/personaje/{nombre}")
async def obtener_personaje(nombre: str, request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)

    nombre = nombre.strip().lower()
    if nombre not in PERSONAJES:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    datos_personaje = PERSONAJES[nombre].copy()
    datos_personaje['preguntas'] = preguntas_restantes.get(nombre, {"anima": 0, "eidolon": 0, "hada": 0, "fantasma": 0})
    return JSONResponse(datos_personaje)

@app.post("/admin/resetear-preguntas")
async def resetear_preguntas(request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)

    data = await request.json()
    nombre = data.get("nombre")
    nombre_lower = nombre.strip().lower()

    if not nombre or nombre_lower not in PERSONAJES:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    preguntas_restantes[nombre_lower] = {"anima": 3, "eidolon": 3, "hada": 3, "fantasma": 3}
    guardar_preguntas()
    return JSONResponse({"mensaje": f"Preguntas de {nombre} reseteadas."})

@app.post("/admin/guardar-preguntas")
async def guardar_preguntas_admin(request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)

    data = await request.json()
    cambios = data.get("cambios", {})
    for nombre, preguntas in cambios.items():
        nombre_lower = nombre.strip().lower()
        preguntas_restantes.setdefault(nombre_lower, {})
        for ia, valor in preguntas.items():
            preguntas_restantes[nombre_lower][ia] = valor
    guardar_preguntas()
    return JSONResponse({"mensaje": "Preguntas actualizadas correctamente."})

# NOTAS

@app.get("/notas")
async def ver_notas(request: Request):
    if 'usuario' not in request.session:
        return RedirectResponse(url="/")
    return FileResponse(os.path.join(BASE_DIR, 'notas', 'index.html'))

@app.route("/notas/contenido", methods=["GET", "POST"])
async def gestionar_notas(request: Request):
    if 'usuario' not in request.session:
        raise HTTPException(status_code=403)

    usuario = request.session['usuario'].lower()
    ruta_nota = os.path.join(BASE_DIR, 'notas', 'usuarios', f'{usuario}.txt')

    if request.method == "GET":
        if os.path.exists(ruta_nota):
            with open(ruta_nota, 'r', encoding='utf-8') as f:
                contenido = f.read()
            return JSONResponse({"contenido": contenido})
        return JSONResponse({"contenido": ""})

    if request.method == "POST":
        data = await request.json()
        contenido = data.get("contenido", "")
        os.makedirs(os.path.dirname(ruta_nota), exist_ok=True)
        with open(ruta_nota, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return JSONResponse({"mensaje": "Notas guardadas correctamente."})

# LOGS

@app.post("/log-evento")
async def log_evento(request: Request):
    if 'usuario' not in request.session:
        raise HTTPException(status_code=403)

    usuario = request.session['usuario'].lower()
    data = await request.json()
    tipo = data.get("tipo")
    contenido = data.get("contenido")
    if not tipo or not contenido:
        raise HTTPException(status_code=400, detail="Faltan datos")

    evento = {"timestamp": datetime.now().isoformat(), "tipo": tipo, "contenido": contenido}
    ruta_log = os.path.join(LOGS_DIR, f"{usuario}.json")
    eventos = []
    if os.path.exists(ruta_log):
        try:
            with open(ruta_log, 'r', encoding='utf-8') as f:
                eventos = json.load(f)
        except Exception:
            eventos = []
    eventos.append(evento)
    with open(ruta_log, 'w', encoding='utf-8') as f:
        json.dump(eventos, f, indent=2, ensure_ascii=False)
    return JSONResponse({"mensaje": "Evento registrado"})

@app.delete("/admin/logs/{nombre}.json")
async def borrar_log_personaje(nombre: str, request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)

    ruta_log = os.path.join(LOGS_DIR, f"{nombre}.json")
    if os.path.exists(ruta_log):
        os.remove(ruta_log)
        return JSONResponse({"mensaje": "Log eliminado correctamente."})
    return JSONResponse({"mensaje": "No hay log que eliminar."})

@app.get("/usos")
async def usos_actuales(request: Request):
    if 'usuario' not in request.session:
        return JSONResponse({})
    cargar_preguntas()
    usuario = request.session['usuario'].lower()
    usos = preguntas_restantes.get(usuario, {})
    return JSONResponse({k.lower(): v for k, v in usos.items()})

# PANEL NARRADOR
@app.get("/panel")
async def panel(request: Request):
    if request.session.get('usuario') != 'narrador':
        return RedirectResponse(url="/")
    return FileResponse(os.path.join(BASE_DIR, 'narrador', 'index.html'))

# CONEXIONES
@app.get("/conexiones")
async def ver_conexiones():
    return FileResponse(os.path.join(BASE_DIR, 'conexiones', 'index.html'))

@app.get("/conexiones/{archivo:path}")
async def static_conexiones(archivo: str):
    return FileResponse(os.path.join(BASE_DIR, 'conexiones', archivo))

@app.route("/conexiones/personajes/{nombre}.json", methods=["GET", "POST"])
async def manejar_conexiones(nombre: str, request: Request):
    ruta = os.path.join(BASE_DIR, 'conexiones', 'personajes', f'{nombre}.json')

    if request.method == "GET":
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                return JSONResponse(json.load(f))
        return JSONResponse({"elements": {"nodes": [], "edges": []}}, status_code=404)

    if request.method == "POST":
        data = await request.json()
        if not data:
            raise HTTPException(status_code=400, detail="No se recibió data válida.")

        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return JSONResponse({"mensaje": f"Archivo {nombre}.json guardado correctamente."})

# ADMIN FICHAS AVANZADO
@app.get("/admin/ficha/{nombre}.json")
async def admin_obtener_ficha_json(nombre: str, request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Ficha no encontrada")

    with open(ruta, 'r', encoding='utf-8') as f:
        return JSONResponse(json.load(f))

@app.post("/admin/ficha/{nombre}.json")
async def admin_guardar_ficha_json(nombre: str, request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    os.makedirs(os.path.dirname(ruta), exist_ok=True)

    nuevo_contenido = await request.json()
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(nuevo_contenido, f, indent=2, ensure_ascii=False)
    return JSONResponse({"mensaje": "Ficha creada o actualizada correctamente."})

@app.patch("/admin/ficha/{nombre}.json")
async def admin_actualizar_ficha_parcial(nombre: str, request: Request):
    if request.session.get('rol') != 'admin':
        raise HTTPException(status_code=403)

    ruta = os.path.join(BASE_DIR, 'ficha', 'personajes', f'{nombre}.json')
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Ficha no encontrada")

    with open(ruta, 'r', encoding='utf-8') as f:
        datos_actuales = json.load(f)

    nuevos_datos = await request.json()

    def actualizar_recursivo(destino, fuente):
        for clave, valor in fuente.items():
            if isinstance(valor, dict) and clave in destino and isinstance(destino[clave], dict):
                actualizar_recursivo(destino[clave], valor)
            else:
                destino[clave] = valor

    actualizar_recursivo(datos_actuales, nuevos_datos)

    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos_actuales, f, ensure_ascii=False, indent=2)

    return JSONResponse({"mensaje": "Campo actualizado correctamente."})

# IA ESTÁTICA Y RUTAS PERSONALIZADAS
@app.get("/{ia}")
async def ia_home(ia: str):
    ia_dir = os.path.join(BASE_DIR, ia)
    return FileResponse(os.path.join(ia_dir, 'index.html'))

@app.get("/{ia}/{archivo:path}")
async def ia_static(ia: str, archivo: str):
    return FileResponse(os.path.join(BASE_DIR, ia, archivo))

@app.post("/{ia}/query")
async def ia_query_ruta(ia: str, request: Request):
    cargar_preguntas()
    data = await request.json()
    mensaje_original = data.get("mensaje", "")
    usuario = data.get("id", "").strip().lower()
    ia = ia.strip().lower()

    if request.session.get('usuario', '').lower() != usuario:
        raise HTTPException(status_code=403, detail="⚠️ Acceso denegado: sesión inválida.")

    restantes = preguntas_restantes.get(usuario, {}).get(ia, 0)
    if restantes != -1 and restantes <= 0:
        return JSONResponse({"respuesta": "⛔ Se acabaron tus preguntas disponibles para esta IA."})

    respuesta = responder_a_usuario(mensaje_original, ia, usuario)
    if restantes != -1:
        preguntas_restantes[usuario][ia] -= 1
        guardar_preguntas()

    return JSONResponse({"respuesta": respuesta})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), reload=True)
