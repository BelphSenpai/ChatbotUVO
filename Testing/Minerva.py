# Minerva
# Autor: Nil López
# Fecha: 2025-03-21
# Versión: 0.2.0
# Descripción: Chatbot con OpenAI que accede a un JSON de worldbuilding filtrado por palabras clave.
# Dependencias: openai, json

#DISCONTINUED, SIN INTEGRACIÓN A DISCORD.PY

import os
import json
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import faiss
from dotenv import load_dotenv

# Inicialización del cliente de OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY")
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
            instructions="Eres Minerva. Responde en menos de 700 caracteres.",
            input=prompt
        )

        # 🔍 Depuración: Ver qué devuelve OpenAI
        print(f"📩 Respuesta de OpenAI: {response}")

        if response and hasattr(response, 'output_text') and response.output_text:
            return response.output_text.strip()
        else:
            print("⚠️ ERROR: OpenAI devolvió una respuesta vacía o None")
            return "[ERROR: OpenAI no generó respuesta]"
    except Exception as e:
        print(f"❌ ERROR en OpenAI: {e}")
        return "[ERROR: No se pudo conectar a OpenAI]"



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
    print("\nMinerva:", respuesta, "\n")

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