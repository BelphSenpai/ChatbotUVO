import subprocess
import os

ias = ["anima", "eidolon", "fantasma", "minerva", "hada"]

SCRIPT_PATH = os.path.join("MinervaPrime", "chunk_generator.py")
BASE_DIR = "MinervaPrime"

for ia in ias:
    print(f"\n🔁 Generando chunks para {ia}...")

    chunk_file = os.path.join(BASE_DIR, f"{ia}_semantic_chunks.json")
    if os.path.exists(chunk_file):
        try:
            os.remove(chunk_file)
            print(f"🗑️ Borrado {chunk_file}")
        except Exception as e:
            print(f"⚠️ Error al borrar {chunk_file}: {e}")
    else:
        print(f"📂 No existía {chunk_file}")

    # Pasamos la IA como argumento directamente
    result = subprocess.run(["python", SCRIPT_PATH, ia])

    if result.returncode != 0:
        print(f"❌ Error al generar chunks para {ia}")
    else:
        print(f"✅ Chunks generados correctamente para {ia}")
