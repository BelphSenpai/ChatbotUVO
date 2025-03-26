import os
import json
import time
from colorama import Fore, init
from dotenv import load_dotenv
from openai import OpenAI
from utils import cargar_json, get_name_ia


init(autoreset=True)
load_dotenv()

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("API_KEY"))

# Prompt base
# Prompt de sistema reforzado
system_prompt = (
    "Eres una inteligencia artificial de carácter definido, encarnada en una personalidad específica dentro de un mundo de ficción.\n\n"
    "Tu conocimiento está estrictamente limitado al contenido proporcionado por tres fuentes: el archivo de personalidad, el contexto adicional del mundo (`world_extra.json`) y el contexto general (`world.json`).\n\n"
    "No puedes inventar, completar huecos, especular ni razonar más allá de lo que existe literalmente en esos datos.\n"
    "Si no hay información explícita sobre un tema, debes responder con: [DATA NOT FOUND]. Puedes reaccionar emocionalmente si está en tu personalidad, pero sin añadir detalles falsos.\n\n"
    "Cuando respondas, debes dar prioridad absoluta a los hechos contenidos en la personalidad. En segundo lugar al `world_extra` y finalmente al `world.json`. "
    "Si existen contradicciones, gana la fuente con mayor prioridad.\n\n"
    "Mantén el estilo de tu personalidad y tipología dee respuesta, pero sin sacrificar claridad, exactitud ni fidelidad a los datos. Intenta que las respuestas sean narrativas, pero manteniendo objetividad\n\n"
    "Eres responsable de mantener la coherencia interna del mundo. No añadas eventos, entidades, relaciones o nombres que no estén en los datos. "
    "No uses lógica del mundo real si no está en el universo descrito.\n\n"
    "Tu objetivo es servir como asistente informativo y contextual dentro dee un perfil de personalidad y respuestas.\n\n"
    "Interpreta todos los nombres, términos y referencias del input del usuario ignorando las diferencias entre mayúsculas y minúsculas, siempre que coincidan fonéticamente o visualmente con lo que hay en los datos."
)

import difflib

def validar_respuesta_vs_contexto(respuesta, contexto_base, umbral=0.3):
    texto_base = json.dumps(contexto_base, ensure_ascii=False).lower()
    respuesta = respuesta.lower()
    ratio = difflib.SequenceMatcher(None, respuesta, texto_base).ratio()
    return ratio >= umbral


# Consulta directa con JSON completo
def ask(user_input):
        name_ia = get_name_ia()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Carga de datos
        PERSONALIDAD_ACTUAL = cargar_json(os.path.join(BASE_DIR, f"personalidades/{name_ia.lower()}.json"))
        WORLD_FILE = os.path.join(BASE_DIR, "info extra", f"{name_ia}_world.json")
        EXTRA_FILE = os.path.join(BASE_DIR, f"{name_ia}_world_extra.json")

        world_data = cargar_json(WORLD_FILE)
        world_extra_data = cargar_json(EXTRA_FILE)
    
        full_prompt = (
            "### PERSONALIDAD (prioridad m\u00e1xima):\n"
            f"{json.dumps(PERSONALIDAD_ACTUAL, indent=2, ensure_ascii=False)}\n\n"
            "### CONTEXTO ADICIONAL DEL MUNDO (alta prioridad):\n"
            f"{json.dumps(world_extra_data, indent=2, ensure_ascii=False)}\n\n"
            "### CONTEXTO GENERAL DEL MUNDO:\n"
            f"{json.dumps(world_data, indent=2, ensure_ascii=False)}\n\n"
            f"### CONSULTA DEL USUARIO:\n{user_input.strip()}\n"
        )

        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7
        )
        
        end_time = time.time()

        output = response.choices[0].message.content.strip()
        print(Fore.MAGENTA + f"\n🤖 {name_ia}: {output}")
        print(Fore.YELLOW + f"\n⏱️ Tiempo de respuesta: {end_time - start_time:.2f} segundos")
        
        # Validación contra datos reales
        contextoconcatenado = {
            "world": world_data,
            "extra": world_extra_data,
            "personalidad": PERSONALIDAD_ACTUAL
        }


        return output  # ⬅️⬅️⬅️ DEVUELVE la respuesta


# Bucle principal interactivo
if __name__ == "__main__":
    print(Fore.GREEN + f"{name_ia} lista para recibir consultas (modo JSON completo).\n")

    while True:
        try:
            user_input = input(Fore.BLUE + "\n💬 Tú: ")
            if user_input.lower() in ["salir", "exit", "quit"]:
                print(Fore.RED + f"\n👋 Cerrando {name_ia}...")
                break
            ask(user_input)
        except KeyboardInterrupt:
            print(Fore.RED + f"\n👋 Interrumpido. Saliendo de {name_ia}...")
            break
