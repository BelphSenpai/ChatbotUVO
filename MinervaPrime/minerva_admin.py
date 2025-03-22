from utils import (
    cargar_json,
    guardar_json,
    aplicar_cambio_a_world,
    registrar_feedback
)

WORLD_PATH = "world.json"
SUGERENCIAS_PATH = "pending_suggestions.json"
FEEDBACK_PATH = "feedback_data.jsonl"

def revisar_sugerencias():
    sugerencias = cargar_json(SUGERENCIAS_PATH)
    nuevas_sugerencias = []

    for sugerencia in sugerencias:
        print("\n📌 Sugerencia:", sugerencia["id"])
        print("Ruta:", " > ".join(sugerencia["ruta"]))
        print("Valor propuesto:", sugerencia["valor"])
        print("Contexto:", sugerencia.get("contexto", "Sin contexto"))

        decision = input("¿Aceptar (a), Rechazar (r), Editar (e), Saltar (s)? ").strip().lower()

        if decision == "a":
            success = aplicar_cambio_a_world(WORLD_PATH, sugerencia["ruta"], sugerencia["valor"])
            if success:
                registrar_feedback(FEEDBACK_PATH, sugerencia, "aceptada")
        elif decision == "r":
            registrar_feedback(FEEDBACK_PATH, sugerencia, "rechazada")
        elif decision == "e":
            print("\n🔧 Editando sugerencia...")
            nuevo_valor = input("✏️ Nuevo valor (deja vacío para mantener el actual): ").strip()
            nueva_ruta_str = input("📍 Nueva ruta (usa punto como separador, deja vacío para mantener la actual): ").strip()

        # Mantener valor actual si no se cambia
            if nuevo_valor:
                try:
                    sugerencia["valor"] = json.loads(nuevo_valor)
                except Exception:
                    sugerencia["valor"] = nuevo_valor

            # Mantener ruta actual si no se cambia
            if nueva_ruta_str:
                sugerencia["ruta"] = nueva_ruta_str.split(".")

         # Aplicar el cambio con la nueva ruta/valor
            success = aplicar_cambio_a_world(WORLD_PATH, sugerencia["ruta"], sugerencia["valor"])
            if success:
                registrar_feedback(FEEDBACK_PATH, sugerencia, "editada")
            elif decision == "s":
                nuevas_sugerencias.append(sugerencia)
            else:
                print("⛔ Opción no válida. Se omite esta sugerencia.")
                nuevas_sugerencias.append(sugerencia)

    guardar_json(SUGERENCIAS_PATH, nuevas_sugerencias)
    print("\n✔️ Revisión finalizada.")

if __name__ == "__main__":
    revisar_sugerencias()
