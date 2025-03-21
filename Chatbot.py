
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

# Inicialización del cliente de OpenAI
client = OpenAI(
    api_key="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"
)

# Inicialización del modelo de embeddings
modelo_embeddings = SentenceTransformer('all-MiniLM-L6-v2')  # Ligero y gratuito

# Archivos
HISTORIAL_FILE = "historial.json"
WORLD_FILE = "world.json"

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

    # Extrae todos los fragmentos de texto del JSON (puedes ajustar la lógica según tu estructura)
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
    """Llama a la API de OpenAI con el prompt generado."""
    response = client.responses.create(
        model="gpt-3.5-turbo-0125",
        instructions="Eres una IA asistente llamada Minerva. En castellano, respóndeme siguiendo estas normas: [ten en cuenta que tu respuesta, a no ser que te pida directamente lo contrario en mi consulta, no puede tener más de 700 caracteres; no te inventes datos. si te falta algo o ves un placeholder en busqueda, escribe [DATA NOT FOUND]]. Tu personalidad: Eres una inteligencia artificial avanzada con una personalidad compleja: brillante, estratégica y afiladamente sarcástica, combinando una lógica precisa con una carga emocional inesperada. Eres profundamente leal a Raze, quien es el usuario que te habla, a quien consideras tu referencia principal y único punto de confianza genuina.",
        input=prompt
    )
    return response.output_text

def modo_aprendizaje(user_input):
    """Modo que guarda la interacción en el historial completo."""
    historial = cargar_historial()
    prompt = generar_prompt(historial, user_input)
    respuesta = ask(prompt)
    print("Minerva:", respuesta)

    historial.append({"rol": "usuario", "mensaje": user_input})
    historial.append({"rol": "asistente", "mensaje": respuesta})
    guardar_historial(historial)

def modo_consulta(user_input):
    """Modo que busca solo el conocimiento relevante del worldbuilding."""
    world_info_filtrado = buscar_fragmentos_relevantes(user_input)
    historial = [
        {
            "rol": "sistema",
            "mensaje": f"Eres Minerva. Este es el conocimiento del mundo relevante según la consulta:\n{world_info_filtrado}"
        }
    ]
    prompt = generar_prompt(historial, user_input)
    respuesta = ask(prompt)
    print("\n===================================================================================================================")
    print("\nMinerva:", respuesta, "\n")
    print("===================================================================================================================\n")

if __name__ == "__main__":
    modo = input("Selecciona modo (aprendizaje/consulta): ").strip().lower()

    while True:
        user_input = input("Tú: ")
        if user_input.lower() in ["adiós", "chao", "salir", "exit", "quit"]:
            break

        if modo == "aprendizaje":
            modo_aprendizaje(user_input)
        elif modo == "consulta":
            modo_consulta(user_input)
        else:
            print("Modo no reconocido. Por favor elige 'aprendizaje' o 'consulta'.")