import sys
import os
from flask import Flask, request, jsonify, render_template
from utils import get_name_ia;
name_ia = get_name_ia()

# Ruta absoluta al proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEB_DIR = os.path.join(BASE_DIR, "www", name_ia)

# Añadir MinervaPrimeSE al path (por si usas Minerva.py)
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from Minerva import responder_a_usuario

# Flask con rutas personalizadas
app = Flask(
    __name__,
    template_folder=WEB_DIR,  # ruta absoluta a hada.html
    static_folder=WEB_DIR,    # ruta absoluta a styles.css
    static_url_path="/"        # sirve archivos estáticos desde la raíz
)

@app.route("/")
def home():
    return render_template(f"{name_ia}.html")

@app.route("/query", methods=["POST"])
def query():
    data = request.json
    mensaje = data["mensaje"]
    ia = data.get("ia", name_ia)
    respuesta = responder_a_usuario(mensaje, ia)
    return jsonify({"respuesta": respuesta})

if __name__ == "__main__":
    app.run(debug=True)
