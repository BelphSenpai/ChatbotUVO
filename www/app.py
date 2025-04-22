# Archivo: www/app.py

import sys
import os
import json
from flask import Flask, request, session, redirect, send_from_directory, jsonify, render_template

# ========== FLASK PRINCIPAL ==========
app = Flask(__name__)
app.secret_key = 'clave-super-secreta'

# Rutas base
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAJES_PATH = os.path.join(BASE_DIR, 'personajes.json')

# Cargar usuarios
with open(PERSONAJES_PATH, 'r') as f:
    PERSONAJES = json.load(f)

# ========== LOGIN / SESSION ==========

from flask import render_template_string

@app.route('/')
def login():
    error = request.args.get('error')
    login_path = os.path.join(BASE_DIR, 'login', 'index.html')
    with open(login_path, 'r', encoding='utf-8') as f:
        template = f.read()
    return render_template_string(template, error=error)


@app.route('/login', methods=['POST'])
def do_login():
    user = request.form.get('usuario', '').lower()
    clave = request.form.get('clave', '')
    datos = PERSONAJES.get(user)
    if datos and datos['clave'] == clave:
        session['usuario'] = user
        return redirect('/panel' if user == 'narrador' else f'/ficha?id={user}')
    return redirect('/?error=Credenciales incorrectas')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ========== FICHA ==========

@app.route('/ficha')
def acceder_ficha():
    if 'usuario' not in session or session['usuario'] == 'narrador':
        return redirect('/')
    path = os.path.join(BASE_DIR, 'ficha')
    return send_from_directory(path, 'index.html')

@app.route('/ficha/personajes/<nombre>.json')
def obtener_personaje_json(nombre):
    path = os.path.join(BASE_DIR, 'ficha', 'personajes')
    return send_from_directory(path, f'{nombre}.json')

# ========== CONEXIONES ==========

@app.route('/conexiones')
def ver_conexiones():
    if 'usuario' not in session or session['usuario'] == 'narrador':
        return redirect('/')
    path = os.path.join(BASE_DIR, 'conexiones')
    return send_from_directory(path, 'index.html')

@app.route('/conexiones/<path:archivo>')
def static_conexiones(archivo):
    path = os.path.join(BASE_DIR, 'conexiones')
    return send_from_directory(path, archivo)

@app.route('/conexiones/personajes/<nombre>.json')
def obtener_conexiones_json(nombre):
    path = os.path.join(BASE_DIR, 'conexiones', 'personajes')
    return send_from_directory(path, f'{nombre}.json')

# ========== PANEL ==========

@app.route('/panel')
def panel():
    if 'usuario' not in session or session['usuario'] != 'narrador':
        return redirect('/')
    path = os.path.join(BASE_DIR, 'narrador')
    archivo = os.path.join(path, 'index.html')
    return send_from_directory(path, 'index.html') if os.path.exists(archivo) else "<h1>Panel del narrador</h1>"

# ========== IA (MinervaPrimeSE embebido) ==========

# IMPORTAR DEPENDENCIAS IA
IA_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'MinervaPrimeSE'))
if IA_DIR not in sys.path:
    sys.path.insert(0, IA_DIR)

from utils import get_name_ia
from Minerva import responder_a_usuario

name_ia = get_name_ia()
IA_WEB_DIR = os.path.join(BASE_DIR, name_ia)  # 📍 importante: las IAs están en /www/{name_ia}

# Ruta: /<ia> → devuelve su HTML
@app.route('/<ia>')
def ia_home(ia):
    ia_dir = os.path.join(BASE_DIR, ia)
    html_path = os.path.join(ia_dir, 'index.html')
    if os.path.exists(html_path):
        return send_from_directory(ia_dir, 'index.html')
    return f"Interfaz para IA '{ia}' no encontrada", 404

# Ruta: /<ia>/<archivo> → sirve assets estáticos como CSS o JS
@app.route('/<ia>/<path:archivo>')
def ia_static(ia, archivo):
    return send_from_directory(os.path.join(BASE_DIR, ia), archivo)

# Ruta: /<ia>/query → llama a la IA correspondiente
# Ruta: /<ia>/query → llama a la IA correspondiente
@app.route('/<ia>/query', methods=['POST'])
def ia_query_ruta(ia):
    data = request.json
    mensaje_original = data.get("mensaje", "")
    usuario = data.get("id", "invitado")
    
    respuesta = responder_a_usuario(mensaje_original, ia, usuario)
    return jsonify({"respuesta": respuesta})



# Ruta genérica: /query
@app.route('/query', methods=['POST'])
def ia_query():
    data = request.json
    mensaje_original = data.get("mensaje", "")
    ia = data.get("ia", name_ia)
    usuario = data.get("id", "invitado")

    respuesta = responder_a_usuario(mensaje_original, ia, usuario)
    return jsonify({"respuesta": respuesta})



# ========== RUN ==========
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

