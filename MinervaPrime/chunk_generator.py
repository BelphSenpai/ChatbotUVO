import os
import sys
import json
import hashlib
from datetime import datetime
from colorama import Fore
from llama_cpp import Llama
from utils import cargar_json, get_name_ia

# -----------------------------
# Obtener nombre de la IA desde argumentos
# -----------------------------
name_ia = get_name_ia()

print(Fore.MAGENTA + f"💡 Procesando IA: {name_ia}")

# -----------------------------
# Configuración de rutas
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LLAMA_MODEL_PATH = os.path.join(BASE_DIR, "models/mistral-7b-instruct-v0.2.Q2_K.gguf")
WORLD_PATH = os.path.join(BASE_DIR, f"{name_ia}_world.json")
CHUNKS_PATH = os.path.join(BASE_DIR, f"{name_ia}_semantic_chunks.json")
HASH_PATH = os.path.join(BASE_DIR, f"{name_ia}_chunks.hash")

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

def transformar_chunks():
    print("🔄 Transformando semantic_chunks.json a formato estructurado...")

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        lineas = json.load(f)

    chunks_transformados = []
    for linea in lineas:
        if ":" in linea:
            ruta_str, texto = linea.split(":", maxsplit=1)
            ruta_limpia = ruta_str.strip().replace(" ", "_").replace(":", ".").lower()
            ruta_lista = ruta_limpia.split(".")
            texto = texto.strip()

            encabezado = ""
            ruta_final = ruta_lista[-1] if ruta_lista else ""
            if "gigantes_conocidos" in ruta_lista:
                encabezado = f"🌋 {ruta_final.replace('_', ' ').title()}: "
            elif "espíritus_conocidos" in ruta_lista:
                encabezado = f"🌀 {ruta_final.replace('_', ' ').title()}: "
            elif "personajes" in ruta_lista:
                encabezado = f"👤 {ruta_final.replace('_', ' ').title()}: "
            elif "facciones" in ruta_lista and "nombre" not in ruta_final:
                encabezado = f"🏴 {ruta_final.replace('_', ' ').title()}: "
            elif "eventos_recientes" in ruta_lista or "fechas_historicas" in ruta_lista:
                encabezado = f"🕒 Evento: "
            elif "objetos" in ruta_lista:
                encabezado = f"📦 {ruta_final.replace('_', ' ').title()}: "

            chunks_transformados.append({
                "ruta": ruta_lista,
                "texto": encabezado + texto
            })

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks_transformados, f, ensure_ascii=False, indent=2)

    print("✅ Chunks estructurados correctamente para FAISS.")

# -----------------------------
# Main
# -----------------------------
def main():
    if not os.path.exists(WORLD_PATH):
        print(Fore.RED + f"❌ No se encuentra {WORLD_PATH}")
        return

    if not necesita_reindexar():
        print(Fore.GREEN + "✅ No hay cambios. No es necesario reindexar.")
        if not os.path.exists(CHUNKS_PATH) or os.stat(CHUNKS_PATH).st_size == 0:
            print(Fore.YELLOW + "📂 No se encontró semantic_chunks.json o está vacío. Generando desde world.json (modo fallback)...")
            world_data = cargar_json(WORLD_PATH)
            semantic_chunks = flatten_json_to_text(world_data)
            with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
                json.dump(semantic_chunks, f, ensure_ascii=False, indent=2)
            print(Fore.GREEN + "✅ semantic_chunks.json generado desde world.json (modo fallback).")
        return

    with open(WORLD_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(Fore.YELLOW + "⏳ Generando chunks por secciones...")
    chunks = generar_chunks_por_seccion(data)

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    guardar_hash_actual()
    print(Fore.GREEN + f"✅ {len(chunks)} chunks guardados en {CHUNKS_PATH} ({datetime.now().strftime('%H:%M:%S')})")

    transformar_chunks()

if __name__ == "__main__":
    main()
