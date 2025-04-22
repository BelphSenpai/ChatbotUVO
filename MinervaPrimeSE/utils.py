import json
import os
import re
from colorama import Fore
import colorama
from dotenv import load_dotenv

colorama.init(autoreset=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv()

name_ia = os.getenv("NAME")

def cargar_json(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def guardar_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def registrar_feedback(path, sugerencia, decision):
    registro = {
        "id": sugerencia["id"],
        "ruta": sugerencia["ruta"],
        "valor": sugerencia["valor"],
        "contexto": sugerencia.get("contexto", ""),
        "decision": decision
    }
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(registro, ensure_ascii=False) + '\n')

def aplicar_cambio_a_world(filepath, ruta, nuevo_valor):
    # 🔍 LIMPIEZA si el valor es un string que contiene un bloque markdown con JSON
    if isinstance(nuevo_valor, str):
        bloque = re.search(r"```json\s*(.*?)\s*```", nuevo_valor, re.DOTALL)
        if bloque:
            contenido = bloque.group(1)
            try:
                nuevo_valor = json.loads(contenido)
                print("🔄 Valor convertido desde bloque markdown a JSON.")
            except Exception as e:
                print(f"⚠️ No se pudo parsear el bloque como JSON: {e}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ref = data
    for i, paso in enumerate(ruta[:-1]):
        if isinstance(ref, list):
            # Buscar por 'id' o 'nombre' ignorando mayúsculas
            match = None
            for elem in ref:
                if isinstance(elem, dict) and (
                    elem.get("id", "").lower() == paso.lower() or
                    elem.get("nombre", "").lower() == paso.lower()
                ):
                    match = elem
                    break
            if not match:
                print(f"⚠ No se encontró '{paso}' en la lista. Se creará una entrada nueva.")
                match = {"id": paso}
                ref.append(match)
            ref = match
        else:
            if paso not in ref:
                print(f"⚠ La clave '{paso}' no existe. Se crea automáticamente.")
                ref[paso] = {}
            ref = ref[paso]

    clave_final = ruta[-1]
    if isinstance(ref, list):
        # Si es una lista, se añade un nuevo dict con 'id' y el valor
        nuevo_objeto = {
            "id": clave_final
        }
        if isinstance(nuevo_valor, dict):
            nuevo_objeto.update(nuevo_valor)
        else:
            nuevo_objeto["valor"] = nuevo_valor
        ref.append(nuevo_objeto)
        print(f"📥 Añadido a lista con id='{clave_final}' → {nuevo_objeto}")
    else:
        ref[clave_final] = nuevo_valor
        print(f"✅ Modificación aplicada: {'.'.join(ruta)} → {nuevo_valor}")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True

def flatten_json(obj, prefix=""):
    """
    Convierte un JSON anidado en un diccionario plano con claves jerárquicas.
    Ej: {"a": {"b": 1}} -> {"a.b": 1}
    """
    flat = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}{k}" if prefix == "" else f"{prefix}.{k}"
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

def set_name_ia(nombre):
    global name_ia, PERSONALIDAD_ACTUAL, instrucciones_globales
    name_ia = nombre

    print(Fore.CYAN + f"📛 Cambiando nombre de IA a: {name_ia}")

    path = os.path.join(f"personalidades", f"{name_ia.lower()}.json")
    with open(path, "r", encoding="utf-8") as f:
        PERSONALIDAD_ACTUAL = json.load(f)

def get_name_ia():
    if name_ia is None:
        set_name_ia(os.getenv("NAME"))
    return name_ia