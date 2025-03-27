import os
import sys
import json
import hashlib
from datetime import datetime
from colorama import Fore
from llama_cpp import Llama
from utils import cargar_json, get_name_ia

import time

inicio = time.time()
# -----------------------------
# Obtener nombre de la IA desde argumentos
# -----------------------------
if len(sys.argv) > 1:
    name_ia = sys.argv[1].lower()
else:
    name_ia = get_name_ia()

print(Fore.MAGENTA + f"💡 Procesando IA: {name_ia}")

# -----------------------------
# Configuración de rutas
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LLAMA_MODEL_PATH = os.path.join(BASE_DIR, "models/mistral-7b-instruct-v0.2.Q2_K.gguf")
WORLD_PATH = os.path.join("world", f"{name_ia}_world.json")
CHUNKS_PATH = os.path.join(BASE_DIR, "semantic chunks", f"{name_ia}_semantic_chunks.json")
HASH_PATH = os.path.join(BASE_DIR, "semantic chunks", f"{name_ia}_chunks.hash")

# -----------------------------
# Inicializa LlamaCpp
# -----------------------------
llm = Llama(
    model_path=LLAMA_MODEL_PATH,
    n_ctx=2048,
    n_threads=8,
    temperature=0.2,
    top_p=0.95,
    verbose=False,
)

PROMPT_EXPLICATIVO = (
    "Convierte este JSON en frases humanas claras y completas. No resumas ni elimines datos. "
    "Incluye todos los campos, y si hay clasificaciones, enuméralas. Usa un estilo neutral.\n\nEntrada:\n{json}\n\nFrases:"
)

# -----------------------------
# Utilidades
# -----------------------------
def hash_archivo(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def necesita_reindexar(world_path=WORLD_PATH, hash_path=HASH_PATH):
    world_hash = hash_archivo(world_path)
    if not os.path.exists(hash_path):
        return True
    with open(hash_path, "r") as f:
        return world_hash != f.read().strip()

def guardar_hash_actual(world_path=WORLD_PATH, hash_path=HASH_PATH):
    h = hash_archivo(world_path)
    with open(hash_path, "w") as f:
        f.write(h)

def generar_frase_llm(obj):
    entrada = json.dumps(obj, ensure_ascii=False, indent=2)
    if len(entrada) > 3000:
        print(Fore.YELLOW + "⚠️ Entrada demasiado larga. Usando modo seguro (flatten).")
        return None
    prompt = PROMPT_EXPLICATIVO.format(json=entrada)
    try:
        output = llm(prompt, max_tokens=512, stop=["\n"])
        return output['choices'][0]['text'].strip()
    except Exception as e:
        print(Fore.RED + f"❌ Error con LLM: {e}")
        return None

def flatten_json_to_text(obj, prefix=""):
    textos = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            nueva_ruta = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                textos.extend(flatten_json_to_text(v, nueva_ruta))
            else:
                ruta_lista = nueva_ruta.split(".")
                textos.append({"ruta": ruta_lista, "texto": f"{v}"})
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            nueva_ruta = f"{prefix}[{i}]"
            textos.extend(flatten_json_to_text(item, nueva_ruta))
    return textos

def generar_chunks_por_seccion(json_data):
    chunks = []
    for seccion, contenido in json_data.items():
        print(Fore.CYAN + f"🔍 Procesando sección: {seccion}")
        def recorrer(obj):
            if isinstance(obj, dict):
                texto = generar_frase_llm(obj)
                if texto and len(texto.split()) >= 5:
                    chunks.append(texto)
                else:
                    chunks.extend(flatten_json_to_text(obj))
            elif isinstance(obj, list):
                for item in obj:
                    recorrer(item)
        recorrer(contenido)
    return chunks

def transformar_chunks(path=CHUNKS_PATH, es_extra=False):
    print(f"🔄 Transformando {os.path.basename(path)} a formato estructurado...")

    is_extra = es_extra or ("extra" in os.path.basename(path))

    with open(path, "r", encoding="utf-8") as f:
        lineas = json.load(f)

    chunks_transformados = []
    for linea in lineas:
        if ":" in linea:
            ruta_str, texto = linea.split(":", maxsplit=1)
            ruta_limpia = ruta_str.strip().replace(" ", "_").replace(":", ".").lower()
            ruta_lista = ruta_limpia.split(".")
            texto = texto.strip()
        else:
            ruta_lista = linea.get("ruta", [])
            texto = linea.get("texto", "").strip()
            if not ruta_lista or not texto:
                continue

        encabezado = ""
        ruta_final = ruta_lista[-1] if ruta_lista else ""

        if "gigantes_conocidos" in ruta_lista:
            encabezado = f"🌋 {ruta_final.replace('_', ' ').title()}: "
        elif "espíritus_conocidos" in ruta_lista:
            encabezado = f"🌀 {ruta_final.replace('_', ' ').title()}: "
        elif "personajes" in ruta_lista:
            encabezado = f"👤 {ruta_final.replace('_', ' ').title()}: "
        elif "facciones" in ruta_lista and "nombre" not in ruta_final.lower():
            encabezado = f"🏴 {ruta_final.replace('_', ' ').title()}: "
        elif "eventos_recientes" in ruta_lista or "fechas_historicas" in ruta_lista:
            encabezado = f"🕒 Evento: "
        elif "objetos" in ruta_lista:
            encabezado = f"📦 {ruta_final.replace('_', ' ').title()}: "
        elif any(palabra in ruta_final.lower() for palabra in ["camino", "campo", "sendero"]):
            encabezado = f"✨ {ruta_final.replace('_', ' ').title()}: "
        elif "esteticas" in ruta_lista:
            encabezado = f"🎭 {ruta_final.replace('_', ' ').title()}: "
        elif "rituales" in ruta_lista:
            encabezado = f"🪄 {ruta_final.replace('_', ' ').title()}: "
        elif "historia" in ruta_lista:
            encabezado = f"📖 {ruta_final.replace('_', ' ').title()}: "
        elif "ancestros" in ruta_lista:
            encabezado = f"👣 {ruta_final.replace('_', ' ').title()}: "

        if is_extra:
            texto = f"[PRIORIDAD EXTRA] {texto}"

        chunks_transformados.append({
            "ruta": ruta_lista,
            "texto": encabezado + texto,
            **({"es_extra": True} if is_extra else {})
        })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks_transformados, f, ensure_ascii=False, indent=2)

    print(f"✅ Chunks estructurados guardados en {path}")

    # Solo sobrescribe el archivo normal si no estamos procesando los extras
    if not is_extra:
        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(chunks_transformados, f, ensure_ascii=False, indent=2)
    print("✅ Chunks estructurados correctamente para FAISS.")

def generar_chunks_extraworld(nombre_ia, input_path=None, output_path=None, aplicar_transformacion=True):
    """
    Genera el archivo de chunks extra `{nombre_ia}_extra_semantic_chunks.json` desde un archivo extraworld JSON (estructurado o plano).
    """
    print(Fore.CYAN + f"📦 Generando chunks extra para {nombre_ia}...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = input_path or os.path.join(base_dir, f"extraworld_{nombre_ia}.json")
    output_path = output_path or os.path.join(base_dir, f"{nombre_ia}_extra_semantic_chunks.json")

    if not os.path.exists(input_path):
        print(Fore.RED + f"❌ No se encontró el archivo de entrada: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Detectar si ya está chunkificado
    if isinstance(data, list) and all("ruta" in c and "texto" in c for c in data):
        chunks = data
        print(Fore.GREEN + f"🧩 {len(chunks)} chunks ya formateados detectados.")
    else:
        print(Fore.YELLOW + "🔄 Formateando JSON a chunks planos...")
        chunks = flatten_json_to_text(data)

    # Marcar todos como extra
    for chunk in chunks:
        chunk["es_extra"] = True

    if aplicar_transformacion:
        print(Fore.BLUE + "🎨 Aplicando transformación estructural (encabezados)...")
        chunks = transformar_chunks_en_memoria(chunks, aplicar_encabezado=False)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(Fore.GREEN + f"✅ Chunks extra guardados en {output_path} ({len(chunks)} entradas).")
    return chunks  # Devuelve los chunks por si los quieres usar directamente

def transformar_chunks_en_memoria(chunks, aplicar_encabezado=True):
    chunks_transformados = []

    for chunk in chunks:
        ruta = chunk.get("ruta", [])
        texto = chunk.get("texto", "").strip()
        if not texto:
            continue

        encabezado = ""
        ruta_final = ruta[-1] if ruta else ""

        if aplicar_encabezado:
            if "gigantes_conocidos" in ruta:
                encabezado = f"🌋 {ruta_final.replace('_', ' ').title()}: "
            elif "espíritus_conocidos" in ruta:
                encabezado = f"🌀 {ruta_final.replace('_', ' ').title()}: "
            elif "personajes" in ruta:
                encabezado = f"👤 {ruta_final.replace('_', ' ').title()}: "
            elif "facciones" in ruta and "nombre" not in ruta_final:
                encabezado = f"🏴 {ruta_final.replace('_', ' ').title()}: "
            elif "eventos_recientes" in ruta or "fechas_historicas" in ruta:
                encabezado = f"🕒 Evento: "
            elif "objetos" in ruta:
                encabezado = f"📦 {ruta_final.replace('_', ' ').title()}: "

        if chunk.get("es_extra", False):
            texto = f"[PRIORIDAD EXTRA] {texto}"

        chunks_transformados.append({
            "ruta": ruta,
            "texto": encabezado + texto,
            **({"es_extra": True} if chunk.get("es_extra", False) else {})
        })

    return chunks_transformados




# -----------------------------
# Main
# -----------------------------
def main():
    # --- WORLD ---
    if not os.path.exists(WORLD_PATH):
        print(Fore.RED + f"❌ No se encuentra {WORLD_PATH}")
    else:
        if not necesita_reindexar(WORLD_PATH, HASH_PATH):
            print(Fore.GREEN + "✅ No hay cambios en world.json. No es necesario reindexar.")
            if not os.path.exists(CHUNKS_PATH) or os.stat(CHUNKS_PATH).st_size == 0:
                print(Fore.YELLOW + "📂 semantic_chunks.json no encontrado o vacío. Generando desde world.json (modo fallback)...")
                world_data = cargar_json(WORLD_PATH)
                semantic_chunks = flatten_json_to_text(world_data)
                with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
                    json.dump(semantic_chunks, f, ensure_ascii=False, indent=2)
                print(Fore.GREEN + "✅ semantic_chunks.json generado desde world.json (fallback).")
        else:
            with open(WORLD_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(Fore.YELLOW + "⏳ Generando chunks desde world.json...")
            chunks = generar_chunks_por_seccion(data)

            with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)

            guardar_hash_actual(WORLD_PATH, HASH_PATH)
            print(Fore.GREEN + f"✅ {len(chunks)} chunks guardados en {CHUNKS_PATH} ({datetime.now().strftime('%H:%M:%S')})")

            transformar_chunks()

    # --- EXTRAWORLD ---

    extra_path = os.path.join("info extra", f"{name_ia}_extraworld.json")
    extra_chunks_path = os.path.join(BASE_DIR, "semantic chunks", f"{name_ia}_extra_semantic_chunks.json")
    extra_hash_path = os.path.join(BASE_DIR, "semantic chunks", f"{name_ia}_extra_chunks.hash")

    if not os.path.exists(extra_path):
        print(Fore.YELLOW + f"ℹ️ No se encontró extraworld_{name_ia}.json, se omite.")
    else:
        if not necesita_reindexar(extra_path, extra_hash_path):
            print(Fore.GREEN + "✅ No hay cambios en extraworld. No es necesario reindexar.")
            if not os.path.exists(extra_chunks_path) or os.stat(extra_chunks_path).st_size == 0:
                print(Fore.YELLOW + "📂 extra_semantic_chunks.json no encontrado o vacío. Generando desde extraworld (fallback)...")
                data = cargar_json(extra_path)
                chunks = flatten_json_to_text(data)
                os.makedirs(os.path.dirname(extra_chunks_path), exist_ok=True)
                for c in chunks:
                    c["es_extra"] = True
                with open(extra_chunks_path, "w", encoding="utf-8") as f:
                    json.dump(chunks, f, ensure_ascii=False, indent=2)
                print(Fore.GREEN + f"✅ {len(chunks)} chunks extra generados (fallback).")
        else:
            data = cargar_json(extra_path)

            if isinstance(data, list) and all("ruta" in c and "texto" in c for c in data):
                chunks = data
                print(Fore.GREEN + f"🧩 {len(chunks)} chunks ya formateados detectados en extraworld.")
            else:
                print(Fore.YELLOW + "🔄 Formateando extraworld en chunks planos...")
                chunks = flatten_json_to_text(data)

            for c in chunks:
                c["es_extra"] = True

            with open(extra_chunks_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)

            guardar_hash_actual(extra_path, extra_hash_path)
            print(Fore.GREEN + f"✅ {len(chunks)} chunks guardados en {extra_chunks_path} ({datetime.now().strftime('%H:%M:%S')})")

            transformar_chunks(extra_chunks_path, es_extra=True)

if __name__ == "__main__":
    main()
    print(Fore.GREEN + f"🌟 Chunks generados correctamente para {name_ia}")
    fin = time.time()
    print(f"⏱️ Chunks de {name_ia} generados en: {fin - inicio:.2f} segundos")

