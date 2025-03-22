import json
import os
import re


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