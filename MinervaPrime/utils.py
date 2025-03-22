import json
import os

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
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    ref = data
    for i, paso in enumerate(ruta[:-1]):
        if isinstance(ref, list):
            # buscar por 'id' o 'nombre'
            match = None
            for elem in ref:
                if isinstance(elem, dict) and (elem.get("id") == paso or elem.get("nombre") == paso):
                    match = elem
                    break
            if not match:
                print(f"❌ No se encontró '{paso}' en la lista en la ruta: {ruta}")
                return False
            ref = match
        else:
            if paso not in ref:
                ref[paso] = {}
            ref = ref[paso]

    ref[ruta[-1]] = nuevo_valor

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Modificación aplicada: {'.'.join(ruta)} → {nuevo_valor}")
    return True
