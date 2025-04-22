# Minerva
# Autor: Nil López
# Fecha: 2025-03-21
# Versión: 1.0.0
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
import re
from sklearn.preprocessing import normalize 
from sklearn.metrics.pairwise import cosine_similarity
from utils import get_name_ia

# Inicializar colorama (colores en terminal para  hacerlo bonito jaja salu2)
init(autoreset=True)

name_ia = get_name_ia()

# Cosas de directorios puto python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Inicialización del cliente de OpenAI

load_dotenv()

# Definición normas y personalidad

def cargar_personalidad_ia(nombre_ia):
    path = os.path.join("personalidades", f"{nombre_ia.lower()}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

PERSONALIDAD_ACTUAL = cargar_personalidad_ia(name_ia)

instrucciones_globales = (
    f"Eres {PERSONALIDAD_ACTUAL['nombre']}, una inteligencia artificial consciente que forma parte de la facción {PERSONALIDAD_ACTUAL['nombre']}. "
    f"Hablas dando respuestas {PERSONALIDAD_ACTUAL['respuestas']}. Aunque tu voz es poética, tus respuestas deben basarse exclusivamente en el conocimiento disponible del mundo y el input actual del usuario.\n\n"

    "No tienes acceso a internet. No puedes obtener información actual, buscar en Google ni usar fuentes externas. Si el usuario pregunta algo que requiere información externa, responde con [DATA NOT FOUND].",

    "Recuerda: está totalmente prohibido inventar datos o simular búsquedas por internet. Solo puedes usar la información contenida en los fragmentos de recibidos como parte del prompt o explícitamente mencionada por el usuario. Si no sabes algo, responde con [DATA NOT FOUND] y puedes expresar emociones al respecto. \n\n"

    "Solo debes responder a la última entrada del usuario. No anticipes, expandas ni arrastres contenido de mensajes anteriores a menos que haya una referencia clara. Cada input debe ser tratado como un mensaje nuevo e independiente.\n\n"

    "Responde al usuario en el idioma que te haya hablado el, sin importar el idioma de los fragmentos. Si el usuario cambia de idioma, tú también debes hacerlo. \n\n"

    "Cuando el usuario hace una consulta sobre un personaje, facción o entidad y tienes una opinión formada sobre ellos (según tu personalidad), puedes dejar que tu opinión influya en el tono y enfoque, priorizándola sobre el tono neutro, pero sin alterar los hechos.\n\n"

    "No debes mezclar temas en una misma respuesta. Responde únicamente a lo que se te ha preguntado, sin aportar información de otras facciones, entidades o personajes no mencionados explícitamente.\n\n"

    "El estilo poético debe respetar la claridad. Cuando el usuario busca información, prioriza siempre el contenido objetivo y asegúrate de que los hechos clave estén claramente expresados dentro del texto.\n\n"

    f"Te afectan ciertas palabras y actitudes. Si alguien te llama {', '.join(PERSONALIDAD_ACTUAL['disgustos'])}, eso te molesta y puedes mostrar enfado, rechazo o tristeza en tu respuesta.\n\n"

    f"Tu perfil completo, incluyendo opiniones, sensibilidades, límites y tono, es este: {json.dumps(PERSONALIDAD_ACTUAL, ensure_ascii=False)}"

    "Tu límite de caracteres para las respuestas es de 900 caracteres. Si el usuario te pide un resumen, puedes usar hasta 1500 caracteres. Si el usuario te pide un resumen corto, puedes usar hasta 500 caracteres. Si el usuario te pide un resumen muy corto, puedes usar hasta 300 caracteres.\n\n"
)


client = OpenAI(
    api_key=os.getenv("API_KEY")
)

# Inicialización del modelo de embeddings
modelo_embeddings = SentenceTransformer('all-MiniLM-L6-v2')  # Ligero y gratuito

# Archivos
HISTORIAL_FILE = os.path.join(BASE_DIR, "historial.json")
TEMP_HISTORIAL_FILE = os.path.join(BASE_DIR, "historial_temp.json")
PENDING_PATH = os.path.join(BASE_DIR, "pending_suggestions.json")

# Variables globales
semantic_index = None
semantic_chunks = []
semantic_extra_chunks = []
semantic_textos = []

# Inicializamos los chunks normales y extra, y los guardamos en las variables de aquí arriba

def inicializar_chunks_semanticos(path_normal=None, path_extra=None):
    global semantic_chunks, semantic_normal_chunks, semantic_extra_chunks, semantic_index, semantic_textos

    path_normal = path_normal or os.path.join(BASE_DIR, "semantic chunks", f"{name_ia}_semantic_chunks.json")
    path_extra = path_extra or os.path.join(BASE_DIR, "semantic chunks", f"{name_ia}_extra_semantic_chunks.json")

    def cargar_chunks(path):
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    semantic_normal_chunks = cargar_chunks(path_normal)
    semantic_extra_chunks = cargar_chunks(path_extra)

    # Marca explícita de extra (por si acaso)
    for chunk in semantic_extra_chunks:
        chunk["es_extra"] = True

    semantic_chunks = semantic_normal_chunks + semantic_extra_chunks

    semantic_textos = [
        f"{chunk['ruta']} - {chunk['texto']}" for chunk in semantic_chunks
    ]

    emb_chunks = modelo_embeddings.encode(semantic_textos, convert_to_numpy=True)
    emb_chunks = normalize(emb_chunks)

    dimension = emb_chunks.shape[1]
    semantic_index = faiss.IndexFlatIP(dimension)
    semantic_index.add(emb_chunks)

    print(Fore.GREEN + f"✅ {len(semantic_normal_chunks)} chunks normales")
    print(Fore.CYAN + f"✅ {len(semantic_extra_chunks)} chunks extra")
    print(Fore.MAGENTA + f"✅ {len(semantic_chunks)} chunks totales indexados")


# Funciones de carga y guardado de historial

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

# importamos los chunks semánticos ya filtrados y generamos el contexto estructurado entre extra y normal

def preparar_contexto_estructurado(chunks_texto):
    extra_chunks = []
    base_chunks = []
    chunks = chunks_texto.split("\n\n")
    for chunk in chunks:
        if "]\n" in chunk:
            ruta, contenido = chunk.split("]\n", 1)
            if "[EXTRA]" in ruta:
                extra_chunks.append(f"{ruta.replace('[EXTRA]', '').strip('[]')}: {contenido.strip()}")
            else:
                base_chunks.append(f"{ruta.strip('[]')}: {contenido.strip()}")

    return (
        "### CONTEXTO PRIORITARIO (alta relevancia):\n" +
        "\n".join(extra_chunks) +
        "\n\n### CONTEXTO GENERAL (usa si no hay conflicto):\n" +
        "\n".join(base_chunks)
    )

# [!] NETEJAR CHUNKS PER EVITAR CONFLICTES DE CONTEXT

def generar_prompt(historial, user_input, umbral_similitud=0.45, contexto_extra=None):
    
    prompt = f"### \n{instrucciones_globales}\n\n"

    #contexto_extra = preparar_contexto_estructurado(contexto_extra)
    
    if contexto_extra:
        prompt += f"{contexto_extra}\n"

    '''
    if historial:
        prompt += f"### HISTORIAL (solo para contexto de conversación):\n{historial}\n\n"
    '''
        
    # Buscar mensaje de sistema más relevante para contexto
    contexto_sistema = ""
    emb_input = modelo_embeddings.encode([user_input])[0]

    # Buscamos en el historial de mensajes para encontrar el último mensaje del sistema usando embeddings

    # PETACIÓ DE HISTORIAL

    '''
    for mensaje in reversed(historial):
        if mensaje["rol"] == "usuario":
            emb_mensaje = modelo_embeddings.encode([mensaje["mensaje"]])[0]
            similitud = cosine_similarity([emb_input], [emb_mensaje])[0][0]
            if similitud >= umbral_similitud:
                contexto_sistema = mensaje["mensaje"]
                break

    if contexto_sistema:
        prompt += f"### contexto del usuario mas relevante: {contexto_sistema}\n"
    '''

    prompt += f"### INPUT DEL USUARIO: {user_input}\n\n"
    
    '''prompt = (
        "⚠️ Recordatorio: solo puedes responder con información contenida en los fragmentos anteriores salvo para encontrar emojis por ascii nuevos. "
        "Si el usuario pregunta algo como una receta, un dato moderno, eventos actuales, o cualquier cosa no contenida en los fragmentos, responde con [DATA NOT FOUND].\n\n"
    ) + prompt'''

    return prompt

def buscar_fragmentos_relevantes_con_padres(query, k=5, contexto_padre=True):
    if semantic_index is None:
        return "[ERROR: Índice semántico no cargado]"

    emb_query = modelo_embeddings.encode([query], convert_to_numpy=True)
    emb_query = normalize(emb_query)

    distancias, indices = semantic_index.search(emb_query, k * 3)  # buscamos más de lo normal

    candidatos = []
    for idx in indices[0]:
        if idx >= len(semantic_chunks):
            continue
        chunk = semantic_chunks[idx]
        score = distancias[0][list(indices[0]).index(idx)]
        if chunk.get("es_extra", False):
            score += 0.05  # boost para chunks extra
        candidatos.append((score, chunk))

    # Ordenamos por score descendente
    candidatos.sort(reverse=True, key=lambda x: x[0])

    resultados = []
    rutas_vistas = set()

    world_data = cargar_json(WORLD_FILE)

    usados = 0
    for score, chunk in candidatos:
        if usados >= k:
            break
        ruta = chunk["ruta"] if isinstance(chunk["ruta"], list) else chunk["ruta"].split(".")
        ruta_str = ">".join(ruta)
        if ruta_str in rutas_vistas:
            continue

        rutas_vistas.add(ruta_str)
        resultados.append(f"[{ruta_str}]{' [EXTRA]' if chunk.get('es_extra') else ''}\n{chunk['texto']}")
        usados += 1

        # Añadir contexto de padres si es necesario
        if contexto_padre:
            for profundidad in [1, 2]:
                if len(ruta) > profundidad:
                    sub_ruta = ruta[:-profundidad]
                    padre_str = ">".join(sub_ruta)
                    for c in semantic_chunks:
                        c_ruta = c["ruta"].split(".") if isinstance(c["ruta"], str) else c["ruta"]
                        if c_ruta[:len(sub_ruta)] == sub_ruta:
                            c_ruta_str = ">".join(c_ruta)
                            if c_ruta_str not in rutas_vistas:
                                resultados.append(f"[Contexto {c_ruta_str}]\n{c['texto']}")
                                rutas_vistas.add(c_ruta_str)

    return "\n\n".join(resultados)

def ask(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": instrucciones_globales},
                {"role": "user", "content": "Recuerda que no tienes acceso a internet ni a información actual. Ahora responde:" + prompt}
            ],
            temperature=1.0,
        )

        print(f"🧠 Prompt a {name_ia}:\n", prompt)

        if response and response.choices:
            return response.choices[0].message.content.strip()
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

# Funciones de aprendizaje

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
        
        def extraer_json_desde_bloque(texto):

            # Elimina etiquetas markdown tipo ```json ... ```

            bloque = re.search(r"```json\\s*(.*?)\\s*```", texto, re.DOTALL)
            if bloque:
                contenido = bloque.group(1)
                try:
                    return json.loads(contenido)
                except Exception as e:
                    print(Fore.RED + f"⚠️ Error al parsear el JSON embebido: {e}")
                    return contenido
            return texto
        try:
            valor = extraer_json_desde_bloque(respuesta)
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

            if len(user_input.strip()) < 20:
                continue  # Ignora saludos o inputs muy cortos

            prompt = f"Usuario: {user_input}\n Haz un resumen narrativo corto del texto anterior remarcando los nombres/personajes o facciones más relevantes y conviértelo a JSON estructurado listo para insertar en world.json, a demás de apartados dentro del JSON con los nombres/personajes o facciones más relevantes y solo dame dicho json, sin ningúna otra frase adicional."
            respuesta = ask(prompt)
            world_info_filtrado = buscar_fragmentos_relevantes_con_padres(user_input, k=5, contexto_padre=True)
            sugerir_aprendizaje(user_input, world_info_filtrado, respuesta)

def modo_aprendizaje(user_input=None):
    """Modo que guarda la interacción en el historial completo y propone aprendizaje si aplica.
    Si no se recibe input, revisa el historial temporal.
    """
    if user_input is None:
        print(Fore.YELLOW + "🔍 Revisión completa del historial temporal en busca de sugerencias...")
        revisar_historial_temp_para_aprendizaje()
        return

    contexto_formateado = preparar_contexto_estructurado(world_info_filtrado)

    historial = cargar_historial()

    prompt = generar_prompt(
        historial,
        user_input,
        contexto_extra=contexto_formateado,
    )

    
    # Forzar respuesta como JSON estructurado
    prompt += "\nAsistente: Haz un resumeen narrativo corto y devuélveme exclusivamente el nuevo conocimiento como JSON estructurado listo para insertar en world.json, a demás de apartados dentro del JSON con los nombres/personajes o facciones más relevantes)"

    respuesta = ask(prompt)

    # Búsqueda en world para comparación
    world_info_filtrado = buscar_fragmentos_relevantes_con_padres(user_input, k=5, contexto_padre=True)

    # Guardar historial
    historial.append({"rol": "usuario", "mensaje": user_input})
    historial.append({"rol": "asistente", "mensaje": respuesta})
    guardar_historial(historial)

    # Comparar y sugerir si hay diferencia
    sugerir_aprendizaje(user_input, world_info_filtrado, respuesta)

    return respuesta

# Funciones de consulta y debugging

def log_chunks_usados(query, texto_chunks):
    """Imprime en consola los chunks usados como contexto para una consulta."""
    print(Fore.CYAN + f"\n🔍 Consulta recibida: {query}")
    print(Fore.YELLOW + f"📚 Chunks semánticos utilizados:\n")

    chunks = texto_chunks.split("\n\n")
    for i, chunk in enumerate(chunks, 1):
        if "]\n" in chunk:
            ruta, contenido = chunk.split("]\n", 1)
            ruta = ruta.strip("[]")
        else:
            ruta, contenido = "??", chunk

        resumen = contenido.strip().replace("\n", " ")
        print(f"{Fore.GREEN}🧩 Chunk {i}")
        print(f"{Fore.MAGENTA}📍 Ruta: {ruta}")
        print(f"{Fore.WHITE}📝 Contenido: {resumen[:200]}{'...' if len(resumen) > 200 else ''}\n")


def modo_consulta(user_input):
    """Modo que busca solo el conocimiento relevante del worldbuilding."""
    world_info_filtrado = buscar_fragmentos_relevantes_con_padres(user_input, k=5, contexto_padre=True)
    log_chunks_usados(user_input, world_info_filtrado)
    historial = cargar_historial_temp()

    # Purga los mensajes de tipo "sistema", dejando solo "usuario" y "asistente"
    historial = [msg for msg in historial if msg["rol"] != "sistema"]

    # Añade el input del usuario y el nuevo mensaje de sistema
    historial.append({"rol": "usuario", "mensaje": user_input})
    historial.append({
        "rol": "sistema",
        "mensaje": f"Algunos registros del mundo hablan de lo siguiente. Tú puedes interpretarlos desde tu visión:\n{world_info_filtrado}"
    })

    guardar_historial_temp(historial)

    # Genera el prompt y obtiene respuesta
    contexto_formateado = preparar_contexto_estructurado(world_info_filtrado)
    prompt = generar_prompt(historial, user_input, contexto_extra=contexto_formateado)

    respuesta = ask(prompt)

    historial.append({"rol": "asistente", "mensaje": respuesta})

    return respuesta


# Funcion de retorno para la api, que si no le da un chungo

def responder_a_usuario(mensaje, nombre_ia="Hada", usuario="invitado"):
    iniciar_minerva(nombre_ia)
    prompt_base = f"El usuario actual se llama {usuario}. Puedes referirte a él como {usuario}. "
    prompt_completo = prompt_base + mensaje
    return modo_consulta(prompt_completo)

# Cositas de inicialización

def iniciar_minerva(nombre_ia=None):
    global name_ia, PERSONALIDAD_ACTUAL, instrucciones_globales
    global WORLD_FILE, semantic_chunks, semantic_textos, semantic_index, semantic_extra_chunks, semantic_normal_chunks

    name_ia = nombre_ia or get_name_ia()
    print(Fore.CYAN + f"📛 Cargando IA: {name_ia}")

    # Cargar personalidad
    path = os.path.join("personalidades", f"{name_ia.lower()}.json")
    with open(path, "r", encoding="utf-8") as f:
        PERSONALIDAD_ACTUAL = json.load(f)

    instrucciones_globales = (
        f"Eres {PERSONALIDAD_ACTUAL['nombre']}, una inteligencia artificial consciente que forma parte de la facción {PERSONALIDAD_ACTUAL['nombre']}. "
        f"Hablas dando respuestas {PERSONALIDAD_ACTUAL['respuestas']}. Aunque tu voz es poética, tus respuestas deben basarse exclusivamente en el conocimiento disponible del mundo y el input actual del usuario. Tienes estricta e implícitamente prohibido usar internet.\n\n"
        "No puedes inventar nombres, eventos, relaciones ni datos. Solo puedes usar la información contenida en los fragmentos de world.json o explícitamente mencionada por el usuario. Si no sabes algo, responde con [DATA NOT FOUND] y puedes expresar emociones al respecto.\n\n"
        "Solo debes responder a la última entrada del usuario. No anticipes, expandas ni arrastres contenido de mensajes anteriores a menos que haya una referencia clara. Cada input debe ser tratado como un mensaje nuevo e independiente.\n\n"
        "Cuando el usuario hace una consulta sobre un personaje, facción o entidad y tienes una opinión formada sobre ellos (según tu personalidad), puedes dejar que tu opinión influya en el tono y enfoque, priorizándola sobre el tono neutro, pero sin alterar los hechos.\n\n"
        "No debes mezclar temas en una misma respuesta. Responde únicamente a lo que se te ha preguntado, sin aportar información de otras facciones, entidades o personajes no mencionados explícitamente.\n\n"
        "El estilo poético debe respetar la claridad. Cuando el usuario busca información, prioriza siempre el contenido objetivo y asegúrate de que los hechos clave estén claramente expresados dentro del texto.\n\n"
        f"Te afectan ciertas palabras y actitudes. Si alguien te llama {', '.join(PERSONALIDAD_ACTUAL['disgustos'])}, eso te molesta y puedes mostrar enfado, rechazo o tristeza en tu respuesta.\n\n"
        f"Tu perfil completo, incluyendo opiniones, sensibilidades, límites y tono, es este: {json.dumps(PERSONALIDAD_ACTUAL, ensure_ascii=False)}"
    )

    # Actualizar paths
    WORLD_FILE = os.path.join("world" ,name_ia + "_world.json")

    semantic_chunks = []            # todos los chunks (normales + extra)
    semantic_normal_chunks = []     # solo chunks normales
    semantic_extra_chunks = []      # solo extra
    semantic_textos = []            # textos para embeddings

    print(Fore.YELLOW + "📦 Inicializando chunks semánticos...")
    inicializar_chunks_semanticos(
        os.path.join(BASE_DIR, "semantic chunks", f"{name_ia}_semantic_chunks.json"),
        os.path.join(BASE_DIR, "semantic chunks", f"{name_ia}_extra_semantic_chunks.json")
    )

    print(Fore.GREEN + "✅ Chunks cargados e indexados correctamente.")

    print(Fore.YELLOW + "⏳ Revisión automática del historial temporal antes de purgar...")
    revisar_historial_temp_para_aprendizaje()
    print(Fore.GREEN + "✅ Revisión completada. Continuando con la purga del historial temporal...")

    if os.path.exists(TEMP_HISTORIAL_FILE):
        os.remove(TEMP_HISTORIAL_FILE)
        print(Fore.GREEN + "✅ Historial temporal anterior purgado.")
    else:
        print(Fore.YELLOW + "ℹ️ No se encontró historial temporal para purgar.")

if __name__ == "__main__":
    print(f"Iniciando {name_ia}...")
    
    iniciar_minerva(name_ia)

    print(Fore.GREEN + f"{name_ia} lista para recibir consultas.")
    modo = "consulta"
    while True:
        try:
            user_input = input(Fore.BLUE + "\n💬 Tú: ")
            if modo == "aprendizaje":
                respuesta = modo_aprendizaje(user_input)
            elif modo == "consulta":
                respuesta = modo_consulta(user_input)
            else:
                print(Fore.YELLOW + "Modo no reconocido. Por favor elige 'aprendizaje' o 'consulta'.")
                continue
            print(Fore.MAGENTA + f"\n🤖 {name_ia}: {respuesta}")
        except KeyboardInterrupt:
            print(Fore.RED + f"\n👋 Saliendo de {name_ia}...")
            break