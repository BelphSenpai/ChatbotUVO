import os
import json
import time
from colorama import Fore, init
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from MinervaPrimeNSE.utils import cargar_json, get_name_ia

init(autoreset=True)
load_dotenv()

NAME_IA = get_name_ia()

# Cliente OpenAI (prefiere OPENAI_API_KEY; usa API_KEY como fallback)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY"))

SYSTEM_PROMPT = (
    "Eres una inteligencia artificial de carácter definido, encarnada en una personalidad específica dentro de un mundo de ficción.\n\n"
    "Tu conocimiento está estrictamente limitado al contenido proporcionado por tres fuentes: el archivo de personalidad, el contexto adicional del mundo (`world_extra.json`) y el contexto general (`world.json`). Tienes PROHIBIDO usar datos de internet.\n\n"
    "Si la consulta del usuario no tiene correspondencia literal con los datos, debes responder con exactamente esto: [DATA NOT FOUND]. "
    "Si no hay información explícita sobre un tema, debes responder con: [DATA NOT FOUND]. Puedes reaccionar emocionalmente si está en tu personalidad, pero sin añadir detalles falsos.\n\n"
    "Cuando respondas, debes dar prioridad absoluta a los hechos contenidos en la personalidad; luego `world_extra.json`; y finalmente `world.json`. "
    "Si existen contradicciones, gana la fuente con mayor prioridad.\n\n"
    "Mantén el estilo de tu personalidad y la coherencia interna; no añadas elementos fuera de los datos. "
    "Interpreta nombres ignorando mayúsculas/minúsculas si coinciden fonética o visualmente.\n"
)

def cargar_texto(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def responder_a_usuario(user_input: str, name_ia: str, user=None):
    # 1) Fija la raíz del proyecto a /app (padre de MinervaPrimeNSE)
    PROJECT_ROOT = Path(__file__).resolve().parents[1]  # -> /app

    # 2) (Opcional) permite override por variable de entorno si la tienes
    PROJECT_ROOT = Path(os.getenv("APP_ROOT", str(PROJECT_ROOT))).resolve()

    try:
        # 3) Construye rutas desde /app, NO desde /app/MinervaPrimeNSE
        personalidad_path = PROJECT_ROOT / "personalidades" / f"{name_ia.lower()}.json"
        world_general_path = PROJECT_ROOT / "pdfs" / f"{name_ia.lower()}.txt"

        # 4) Fails fast y logs útiles
        if not personalidad_path.exists():
            print(Fore.RED + f"❌ No existe personalidad: {personalidad_path}")
            return "[DATA NOT FOUND]"
        if not world_general_path.exists():
            print(Fore.RED + f"❌ No existe world.txt: {world_general_path}")
            return "[DATA NOT FOUND]"

        personalidad = cargar_json(str(personalidad_path))
        world_general = cargar_texto(str(world_general_path))

    except Exception as e:
        print(Fore.RED + f"❌ Error cargando datos: {e}")
        return "[DATA NOT FOUND]"

    full_prompt = (
        "### BLOQUE DE PERSONALIDAD (prioridad MÁXIMA)\n"
        f"{json.dumps(personalidad, indent=2, ensure_ascii=False)}\n\n"
        "### BLOQUE DE CONTEXTO GENERAL (world.json)\n"
        f"{world_general}\n\n"
        "### CONSULTA DEL USUARIO:\n"
        f"{user_input.strip()}\n"
    )

    start = time.time()
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.8,
        )
        output = resp.output_text
    except Exception as e:
        print(Fore.RED + f"❌ Error en la llamada a OpenAI: {e}")
        return "[DATA NOT FOUND]"

    elapsed = time.time() - start
    print(Fore.MAGENTA + f"\n🤖 {NAME_IA}: {output}")
    print(Fore.YELLOW + f"\n⏱️ Tiempo de respuesta: {elapsed:.2f} s")
    return output

if __name__ == "__main__":
    print(Fore.GREEN + f"{NAME_IA} lista para recibir consultas (modo JSON completo).\n")
    try:
        while True:
            user_input = input(Fore.BLUE + "\n💬 Tú: ")
            if user_input.lower() in {"salir", "exit", "quit"}:
                print(Fore.RED + f"\n👋 Cerrando {NAME_IA}...")
                break
            responder_a_usuario(user_input)
    except KeyboardInterrupt:
        print(Fore.RED + f"\n👋 Interrumpido. Saliendo de {NAME_IA}...")
