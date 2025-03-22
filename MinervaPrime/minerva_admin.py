from utils import (
    cargar_json,
    guardar_json,
    aplicar_cambio_a_world,
    registrar_feedback
)
import os
import json
from colorama import Fore, Style, init
from Minerva import revisar_historial_temp_para_aprendizaje

# Inicializar colorama
init(autoreset=True)

# Base directory relativa al script actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas absolutas a los archivos
WORLD_PATH = os.path.join(BASE_DIR, "world.json")
SUGERENCIAS_PATH = os.path.join(BASE_DIR, "pending_suggestions.json")
FEEDBACK_PATH = os.path.join(BASE_DIR, "feedback_data.jsonl")

def revisar_sugerencias():
    sugerencias = cargar_json(SUGERENCIAS_PATH)
    nuevas_sugerencias = []

    print(Fore.CYAN + f"\n📋 Revisión de {len(sugerencias)} sugerencias pendientes:\n")

    for sugerencia in sugerencias:
        print(Fore.YELLOW + "="*50)
        print(Fore.BLUE + "📌 ID:", Fore.WHITE + sugerencia["id"])
        print(Fore.BLUE + "📍 Ruta:", Fore.WHITE + " > ".join(sugerencia["ruta"]))
        print(Fore.BLUE + "📄 Valor propuesto:")
        if isinstance(sugerencia["valor"], str):
            print(Fore.GREEN + sugerencia["valor"])
        else:
            print(Fore.GREEN + json.dumps(sugerencia["valor"], indent=2, ensure_ascii=False))

        print(Fore.BLUE + "🧠 Contexto:", Fore.WHITE + sugerencia.get("contexto", "Sin contexto"))

        decision = input(Fore.MAGENTA + "¿Aceptar (a), Rechazar (r), Editar (e), Saltar (s)? ").strip().lower()

        if decision == "a":
            success = aplicar_cambio_a_world(WORLD_PATH, sugerencia["ruta"], sugerencia["valor"])
            if success:
                registrar_feedback(FEEDBACK_PATH, sugerencia, "aceptada")
                print(Fore.GREEN + "✔ Sugerencia aceptada y aplicada.")
        elif decision == "r":
            registrar_feedback(FEEDBACK_PATH, sugerencia, "rechazada")
            print(Fore.RED + "✘ Sugerencia rechazada.")
        elif decision == "e":
            print(Fore.CYAN + "\n🔧 Editando sugerencia...")
            nuevo_valor = input(Fore.YELLOW + "✏️ Nuevo valor (deja vacío para mantener el actual): ").strip()
            nueva_ruta_str = input(Fore.YELLOW + "📍 Nueva ruta (usa punto como separador, deja vacío para mantener la actual): ").strip()

            if nuevo_valor:
                try:
                    sugerencia["valor"] = json.loads(nuevo_valor)
                except Exception:
                    sugerencia["valor"] = nuevo_valor

            if nueva_ruta_str:
                sugerencia["ruta"] = nueva_ruta_str.split(".")

            success = aplicar_cambio_a_world(WORLD_PATH, sugerencia["ruta"], sugerencia["valor"])
            if success:
                registrar_feedback(FEEDBACK_PATH, sugerencia, "editada")
                print(Fore.GREEN + "✏ Sugerencia editada y aplicada.")
        elif decision == "s":
            nuevas_sugerencias.append(sugerencia)
            print(Fore.YELLOW + "↪ Sugerencia saltada y mantenida en la cola.")
        else:
            nuevas_sugerencias.append(sugerencia)
            print(Fore.RED + "⛔ Opción no válida. Se mantiene la sugerencia sin cambios.")

    guardar_json(SUGERENCIAS_PATH, nuevas_sugerencias)
    print(Fore.CYAN + "\n✔️ Revisión finalizada.")

if __name__ == "__main__":
    print(Fore.YELLOW + "⏳ Revisión automática del historial temporal antes de purgar...")
    revisar_historial_temp_para_aprendizaje()
    print(Fore.GREEN + "✅ Revisión completada. Continuando con la purga del historial temporal...")
    if os.path.exists("historial_temp.json"):
            os.remove("historial_temp.json")
    print(Fore.GREEN + "Historial temporal anterior purgado.")
    revisar_sugerencias()
