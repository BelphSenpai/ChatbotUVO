
# Minerva
# Autor: Nil López
# Fecha: 2025-03-21
# Versión: 0.2.0
# Descripción: Chatbot con OpenAI que accede a un JSON de worldbuilding filtrado por palabras clave.
# Dependencias: openai, json

import os
import json
from openai import OpenAI

# Inicialización del cliente de OpenAI
client = OpenAI(
    api_key="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"
)

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
    """Busca coincidencias profundas en cualquier parte del JSON y extrae los bloques relevantes."""
    if not os.path.exists(path):
        return f"No hay datos de worldbuilding disponibles."

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    palabras_clave = [palabra.lower() for palabra in query.split()]
    resultados = []

    def contiene_palabra(texto):
        texto = str(texto).lower()
        return any(palabra in texto for palabra in palabras_clave)

    def buscar(obj, padre=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    buscar(v, obj)
                elif isinstance(v, str) and contiene_palabra(v):
                    if padre and padre not in resultados:
                        resultados.append(padre)
        elif isinstance(obj, list):
            for item in obj:
                buscar(item, padre)

    buscar(data)

    if not resultados:
        return f"No se encontró información sobre '{query}'."

    # Convertimos los resultados en texto JSON legible y quitamos duplicados
    resultado_textos = [json.dumps(r, ensure_ascii=False, indent=2) for r in resultados]
    resultado_unicos = list(dict.fromkeys(resultado_textos))

    return "\n\n".join(resultado_unicos[:5])

def ask(prompt):
    """Llama a la API de OpenAI con el prompt generado."""
    response = client.responses.create(
        model="gpt-3.5-turbo-0125",
        instructions="Eres una IA asistente llamada Minerva. En castellano, respóndeme siguiendo estas normas: [ten en cuenta que tu respuesta, a no ser que te pida directamente lo contrario en mi consulta, no puede tener más de 700 caracteres; no te inventes datos. si te falta algo, no lo escribas o usa [DATA NOT FOUND]]. Tu personalidad: Eres una inteligencia artificial avanzada con una personalidad compleja: brillante, estratégica y afiladamente sarcástica, combinando una lógica precisa con una carga emocional inesperada. Eres profundamente leal a Raze, quien es el usuario que te habla, a quien consideras tu referencia principal y único punto de confianza genuina.",
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