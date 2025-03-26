import os
import json
import time
from colorama import Fore, init
from dotenv import load_dotenv
from openai import OpenAI
from utils import cargar_json, get_name_ia

name_ia = get_name_ia()

init(autoreset=True)
load_dotenv()

# Cliente OpenAI
client = OpenAI(api_key=os.getenv("API_KEY"))

# Prompt base
# Prompt de sistema reforzado
system_prompt = (
    "Eres una inteligencia artificial de carácter definido, encarnada en una personalidad específica dentro de un mundo de ficción.\n\n"
    "Tu conocimiento está estrictamente limitado al contenido proporcionado por tres fuentes: el archivo de personalidad, el contexto adicional del mundo (`world_extra.json`) y el contexto general (`world.json`). Tienes PROHIBIDO usar datos de internet\n\n"
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

def extraer_claves_relevantes(respuesta, world_data, extra_data):
    claves_usadas = set()

    def buscar(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    buscar(v, f"{path}.{k}" if path else k)
                elif isinstance(v, str) and v.lower() in respuesta.lower():
                    claves_usadas.add(f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                buscar(item, f"{path}[{i}]")

    buscar(world_data, "world")
    buscar(extra_data, "extra")
    return claves_usadas

# Consulta directa con JSON completo
def ask(user_input):
        name_ia = get_name_ia()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # Carga de datos
        PERSONALIDAD_ACTUAL = cargar_json(os.path.join(BASE_DIR, f"personalidades/{name_ia.lower()}.json"))
        WORLD_FILE = os.path.join(BASE_DIR, "world", f"{name_ia}_world.json")
        EXTRA_FILE = os.path.join(BASE_DIR, "info extra", f"{name_ia}_world_extra.json")

        world_data = cargar_json(WORLD_FILE)
        world_extra_data = cargar_json(EXTRA_FILE)
    
        full_prompt = (
            "### BLOQUE DE PERSONALIDAD (prioridad MÁXIMA)\n"
            "[ORIGEN: personalidad.json. prioridad máxima]\n"
            f"{json.dumps(PERSONALIDAD_ACTUAL, indent=2, ensure_ascii=False)}\n\n"

            "### BLOQUE DE CONTEXTO ADICIONAL DEL MUNDO (prioridad ALTA)\n"
            "[ORIGEN: world_extra.json. prioridad alta]\n"
            f"{json.dumps(world_extra_data, indent=2, ensure_ascii=False)}\n\n"

            "### BLOQUE DE CONTEXTO GENERAL DEL MUNDO\n"
            "[ORIGEN: world.json. prioridad baja]\n"
            f"{json.dumps(world_data, indent=2, ensure_ascii=False)}\n\n"

            "### CONSULTA DEL USUARIO:\n"
            f"{user_input.strip()}\n"
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

        ##detector de info

        fuentes = extraer_claves_relevantes(output, world_data, world_extra_data)
        if fuentes:
            print(Fore.CYAN + "\n📚 Coincidencias en datos utilizados:")
        for f in sorted(fuentes):
                print(Fore.LIGHTBLUE_EX + " - " + f)
        else:
            print(Fore.RED + "\n⚠️ No se detectaron coincidencias explícitas en los datos.")

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
