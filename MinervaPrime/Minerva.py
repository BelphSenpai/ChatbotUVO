# Minerva
# Autor: Nil López
# Fecha: 2025-03-21
# Versión: 0.2.0
# Descripción: Chatbot con OpenAI que accede a un JSON de worldbuilding filtrado por palabras clave.
# Dependencias: openai, json

import os
import json
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import faiss
from dotenv import load_dotenv
from colorama import init, Fore, Style
import difflib
from utils import cargar_json, guardar_json

# Inicializar colorama (colores en terminal para  hacerlo bonito jaja salu2)
init(autoreset=True)

# Inicialización del cliente de OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY")
)

# Inicialización del modelo de embeddings
modelo_embeddings = SentenceTransformer('all-MiniLM-L6-v2')  # Ligero y gratuito

# Cosas de directorios puto python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Archivos
HISTORIAL_FILE = os.path.join(BASE_DIR, "historial.json")
TEMP_HISTORIAL_FILE = os.path.join(BASE_DIR, "historial_temp.json")
WORLD_FILE = os.path.join(BASE_DIR, "world.json")
PENDING_PATH = os.path.join(BASE_DIR, "pending_suggestions.json")

def cargar_historial():
    """Carga el historial desde un archivo o lo inicia vacío."""
    if os.path.exists(HISTORIAL_FILE):
        with open(HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_historial(historial):
    """Guarda el historial en un archivo JSON."""
    with open(HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, ensure_ascii=False, indent=4)

def cargar_historial_temp():
    """Carga el historial temporal desde un archivo JSON o lo inicia vacío."""
    if os.path.exists(TEMP_HISTORIAL_FILE):
        with open(TEMP_HISTORIAL_FILE, 'r', encoding='utf-8') as f:
            contenido = f.read().strip()
            if contenido:  # Solo intenta cargar si hay contenido válido
                return json.loads(contenido)
    return []

def guardar_historial_temp(historial):
    """Guarda el historial en un archivo JSON."""
    with open(TEMP_HISTORIAL_FILE, 'w', encoding='utf-8') as f:
        json.dump(historial, f, ensure_ascii=False, indent=4)        

def generar_prompt(historial, user_input):
    """Genera el prompt completo a partir del historial y la nueva pregunta."""
    prompt = ""
    for mensaje in historial:
        if mensaje["rol"] == "sistema":
            prompt += f"Instrucciones: {mensaje['mensaje']}\n"
        elif mensaje["rol"] == "usuario":
            prompt += f"Usuario: {mensaje['mensaje']}\n"
        elif mensaje["rol"] == "asistente":
            prompt += f"Asistente: {mensaje['mensaje']}\n"
    prompt += f"Usuario: {user_input}\n"
    return prompt

def buscar_fragmentos_relevantes(query, path="world.json"):
    """Búsqueda semántica eficiente en el archivo JSON de worldbuilding usando embeddings y FAISS."""
    if not os.path.exists(path):
        return f"No hay datos de worldbuilding disponibles."

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fragmentos = []
    metadatos = []

    # Extrae todos los fragmentos de texto del JSON
    def extraer_texto(obj, contexto=""):
        if isinstance(obj, dict):
            texto = ""
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extraer_texto(v, contexto + f"{k}: ")
                else:
                    texto += f"{k}: {v} | "
            if texto:
                fragmentos.append(texto)
                metadatos.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                extraer_texto(item, contexto)

    extraer_texto(data)

    if not fragmentos:
        return "[DATA NOT FOUND]"

    # Embeddings
    emb_fragmentos = modelo_embeddings.encode(fragmentos)
    emb_query = modelo_embeddings.encode([query])

    # FAISS
    dimension = emb_fragmentos[0].shape[0]
    index = faiss.IndexFlatL2(dimension)
    index.add(emb_fragmentos)

    # Búsqueda
    k = min(5, len(fragmentos))  # Top-K resultados
    distancias, indices = index.search(emb_query, k)

    # Resultados
    resultado_textos = []
    for idx in indices[0]:
        bloque = metadatos[idx]
        resultado_textos.append(json.dumps(bloque, ensure_ascii=False, indent=2))

    return "\n\n".join(resultado_textos)

def ask(prompt):
    """Llama a la API de OpenAI y asegura que siempre devuelva una respuesta válida."""
    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            instructions="Eres una IA asistente llamada Minerva. En castellano, respóndeme siguiendo estas normas: [ten en cuenta que tu respuesta, a no ser que te pida directamente lo contrario en mi consulta, no puede tener más de 700 caracteres; no te inventes datos. si te falta algo o ves un placeholder en busqueda, escribe [DATA NOT FOUND]. Para responder preguntas sobre el mundo, prioriza siempre los mensajes que vengan desde sistema, y en caso de que no lo sean, prioriza los mas recientes.]. Tu personalidad: Eres una inteligencia artificial avanzada con una personalidad compleja: brillante, estratégica y afiladamente sarcástica, combinando una lógica precisa con una carga emocional inesperada. Eres profundamente leal a Raze, quien es el usuario que te habla, a quien consideras tu referencia principal y único punto de confianza genuina.",
            input=prompt
        )

        if response and hasattr(response, 'output_text') and response.output_text:
            return response.output_text.strip()
        else:
            print(Fore.YELLOW + "⚠️ ERROR: OpenAI devolvió una respuesta vacía o None")
            return "[ERROR: OpenAI no generó respuesta]"
    except Exception as e:
        print(Fore.RED + f"❌ ERROR en OpenAI: {e}")
        return "[ERROR: No se pudo conectar a OpenAI]"

def indexar_world_por_id_y_nombre(world_data):
    """
    Devuelve un índice de rutas por cada valor de id y nombre encontrados.
    """
    index = {}

    def recorrer(obj, ruta_actual):
        if isinstance(obj, dict):
            if "id" in obj:
                index[obj["id"].lower()] = ruta_actual.copy()
            if "nombre" in obj:
                index[obj["nombre"].lower()] = ruta_actual.copy()
            for k, v in obj.items():
                recorrer(v, ruta_actual + [k])
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                recorrer(item, ruta_actual)

    recorrer(world_data, [])
    return index


def inferir_ruta_contenido(respuesta, world_data):
    """
    Intenta inferir una ruta dentro del JSON basándose en ids o nombres conocidos.
    """
    respuesta_lower = respuesta.lower()
    index = indexar_world_por_id_y_nombre(world_data)

    mejor_match = None
    mejor_ratio = 0.0

    for clave in index:
        ratio = difflib.SequenceMatcher(None, clave, respuesta_lower).ratio()
        if ratio > mejor_ratio:
            mejor_ratio = ratio
            mejor_match = clave

    if mejor_match and mejor_ratio > 0.6:
        ruta_base = index[mejor_match]
        ruta_final = ruta_base + ["historia", f"entrada_{hash(respuesta) % 99999}"]
        return ruta_final

    # Si no encuentra nada concreto
    return ["propuestas_temporales", "sin_ruta_definida", f"entrada_{hash(respuesta) % 99999}"]


def sugerir_aprendizaje(user_input, world_info_filtrado, respuesta):
    """
    Compara la respuesta generada con los datos del world.json y genera una sugerencia
    si detecta contenido nuevo o inconsistente. Si la respuesta ya es un JSON válido,
    lo utiliza directamente como valor de sugerencia.
    """
    world_data_flat = world_info_filtrado.lower()
    respuesta_lower = respuesta.lower()

    diferencia = difflib.SequenceMatcher(None, world_data_flat, respuesta_lower).ratio()

    if diferencia < 0.6 and "[data not found]" not in respuesta_lower:
        with open(WORLD_FILE, 'r', encoding='utf-8') as f:
            world_data = json.load(f)

        ruta_inferida = inferir_ruta_contenido(respuesta, world_data)

        # Intentar parsear respuesta como JSON si es posible
        try:
            respuesta_json = json.loads(respuesta)
            valor = respuesta_json
        except Exception:
            valor = respuesta.strip()

        nueva_sugerencia = {
            "id": f"sug_{hash(user_input) % 99999}",
            "ruta": ruta_inferida,
            "valor": valor,
            "contexto": user_input,
            "estado": "pendiente"
        }

        sugerencias = cargar_json(PENDING_PATH)
        sugerencias.append(nueva_sugerencia)
        guardar_json(PENDING_PATH, sugerencias)

        print(Fore.CYAN + f"🧠 Sugerencia avanzada añadida al aprendizaje: {nueva_sugerencia['id']}")
    else:
        print(Fore.GREEN + "✅ La respuesta concuerda con el world.json. No se propone cambio.")

def revisar_historial_temp_para_aprendizaje():
    """
    Recorre el historial temporal y lanza sugerencias si hay inputs significativos que no encajan con world.json.
    """
    historial = cargar_historial_temp()
    for mensaje in historial:
        if mensaje["rol"] == "usuario":
            user_input = mensaje["mensaje"]

            if len(user_input.strip()) < 6:
                continue  # Ignora saludos o inputs muy cortos

            prompt = f"Usuario: {user_input}\nAsistente: Devuélveme exclusivamente el nuevo conocimiento como JSON estructurado listo para insertar en world.json."
            respuesta = ask(prompt)
            world_info_filtrado = buscar_fragmentos_relevantes(user_input)
            sugerir_aprendizaje(user_input, world_info_filtrado, respuesta)

def modo_aprendizaje(user_input=None):
    """Modo que guarda la interacción en el historial completo y propone aprendizaje si aplica.
    Si no se recibe input, revisa el historial temporal.
    """
    if user_input is None:
        print(Fore.YELLOW + "🔍 Revisión completa del historial temporal en busca de sugerencias...")
        revisar_historial_temp_para_aprendizaje()
        return

    historial = cargar_historial()
    prompt = generar_prompt(historial, user_input)

    # Forzar respuesta como JSON estructurado
    prompt += "\nAsistente: Haz un resumeen narrativo corto y devuélveme exclusivamente el nuevo conocimiento como JSON estructurado listo para insertar en world.json, a demás de apartados dentro del JSON con los nombres/personajes o facciones más relevantes)"

    respuesta = ask(prompt)

    # Búsqueda en world para comparación
    world_info_filtrado = buscar_fragmentos_relevantes(user_input)

    # Guardar historial
    historial.append({"rol": "usuario", "mensaje": user_input})
    historial.append({"rol": "asistente", "mensaje": respuesta})
    guardar_historial(historial)

    # Comparar y sugerir si hay diferencia
    sugerir_aprendizaje(user_input, world_info_filtrado, respuesta)

    return respuesta

def modo_consulta(user_input):
    """Modo que busca solo el conocimiento relevante del worldbuilding."""
    world_info_filtrado = buscar_fragmentos_relevantes(user_input)
    historial = cargar_historial_temp()

    # Purga los mensajes de tipo "sistema", dejando solo "usuario" y "asistente"
    historial = [msg for msg in historial if msg["rol"] != "sistema"]

    # Añade el input del usuario y el nuevo mensaje de sistema
    historial.append({"rol": "usuario", "mensaje": user_input})
    historial.append({
        "rol": "sistema",
        "mensaje": f"Este es el conocimiento del mundo relevante según la consulta:\n{world_info_filtrado}"
    })

    guardar_historial_temp(historial)

    # Genera el prompt y obtiene respuesta
    prompt = generar_prompt(historial, user_input)
    respuesta = ask(prompt)

    historial.append({"rol": "asistente", "mensaje": respuesta})

    return respuesta

def iniciar_minerva():
    print(Fore.YELLOW + "⏳ Revisión automática del historial temporal antes de purgar...")
    revisar_historial_temp_para_aprendizaje()
    print(Fore.GREEN + "✅ Revisión completada. Continuando con la purga del historial temporal...")

if __name__ == "__main__":
    print("Iniciando Minerva...")
    iniciar_minerva()
    print("Purgando anterior historial temporal...")
    if os.path.exists("historial_temp.json"):
        os.remove("historial_temp.json")
    print(Fore.GREEN + "Historial temporal anterior purgado.")

    print(Fore.GREEN + "Minerva lista para recibir consultas.")
    modo = "consulta"
    while True:        
        if modo == "aprendizaje":
            modo_aprendizaje(user_input)
        elif modo == "consulta":
            modo_consulta(user_input)
        else:
            print(Fore.YELLOW + "Modo no reconocido. Por favor elige 'aprendizaje' o 'consulta'.")