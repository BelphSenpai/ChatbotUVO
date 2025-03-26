import os
import json
import re
from colorama import Fore, init
from dotenv import load_dotenv

# Inicialización
init(autoreset=True)
load_dotenv()

# Variables globales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
name_ia = os.getenv("NAME") or "minerva"

# ----------------------------
# 📦 Carga y Guardado de JSON
# ----------------------------

def cargar_json(path):
    """Carga un archivo JSON si existe, o devuelve una lista vacía."""
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_json(path, data):
    """Guarda datos como JSON en el archivo especificado."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ----------------------------
# 📝 Feedback y Registro
# ----------------------------

def registrar_feedback(path, sugerencia, decision):
    """Registra una decisión de aprendizaje manual (aceptado/rechazado)."""
    registro = {
        "id": sugerencia["id"],
        "ruta": sugerencia["ruta"],
        "valor": sugerencia["valor"],
        "contexto": sugerencia.get("contexto", ""),
        "decision": decision
    }
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(registro, ensure_ascii=False) + '\n')

# ----------------------------
# 🔧 Aplicar Cambios a world.json
# ----------------------------

def aplicar_cambio_a_world(filepath, ruta, nuevo_valor):
    """
    Aplica un cambio a un JSON dado, creando claves o listas intermedias si es necesario.
    Soporta valores con bloques tipo ```json {...}```.
    """
    # Si el valor es un string con JSON embebido, intenta parsearlo
    if isinstance(nuevo_valor, str):
        bloque = re.search(r"```json\s*(.*?)\s*```", nuevo_valor, re.DOTALL)
        if bloque:
            try:
                nuevo_valor = json.loads(bloque.group(1))
                print(Fore.CYAN + "🔄 Valor convertido desde bloque markdown a JSON.")
            except Exception as e:
                print(Fore.RED + f"⚠️ Error al parsear bloque JSON: {e}")

    # Cargar el archivo actual
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ref = data
    for paso in ruta[:-1]:
        if isinstance(ref, list):
            match = next((e for e in ref if isinstance(e, dict) and (
                e.get("id", "").lower() == paso.lower() or e.get("nombre", "").lower() == paso.lower()
            )), None)
            if not match:
                print(Fore.YELLOW + f"⚠ No se encontró '{paso}' en la lista. Se crea.")
                match = {"id": paso}
                ref.append(match)
            ref = match
        else:
            ref = ref.setdefault(paso, {})

    clave_final = ruta[-1]

    if isinstance(ref, list):
        nuevo_objeto = {"id": clave_final}
        if isinstance(nuevo_valor, dict):
            nuevo_objeto.update(nuevo_valor)
        else:
            nuevo_objeto["valor"] = nuevo_valor
        ref.append(nuevo_objeto)
        print(Fore.GREEN + f"📥 Añadido a lista: {clave_final}")
    else:
        ref[clave_final] = nuevo_valor
        print(Fore.GREEN + f"✅ Cambio aplicado: {'.'.join(ruta)}")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True

# ----------------------------
# 🔍 Utilidades Extra
# ----------------------------

def flatten_json(obj, prefix=""):
    """
    Convierte un JSON anidado en un diccionario plano con claves jerárquicas.
    Ej: {"a": {"b": 1}} -> {"a.b": 1}
    """
    flat = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            if isinstance(v, (dict, list)):
                flat.update(flatten_json(v, new_key))
            else:
                flat[new_key] = v
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_key = f"{prefix}[{i}]"
            if isinstance(item, (dict, list)):
                flat.update(flatten_json(item, new_key))
            else:
                flat[new_key] = item
    return flat

# ----------------------------
# 🔄 Nombre y Personalidad
# ----------------------------

def get_name_ia():
    """Devuelve el nombre de la IA actual."""
    return name_ia

def set_name_ia(nombre):
    """Cambia el nombre de la IA y recarga su personalidad."""
    global name_ia, PERSONALIDAD_ACTUAL
    name_ia = nombre
    print(Fore.CYAN + f"📛 IA activa: {name_ia}")

    path = os.path.join(BASE_DIR, f"personalidades/{name_ia.lower()}.json")
    with open(path, "r", encoding="utf-8") as f:
        PERSONALIDAD_ACTUAL = json.load(f)
