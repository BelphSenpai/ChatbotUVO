import subprocess
import os

ias = ["anima", "eidolon", "fantasma", "minerva", "hada"]

SCRIPT_PATH = os.path.join("MinervaPrime", "chunk_generator.py")
BASE_DIR = "MinervaPrime"

for ia in ias:
    print(f"\n🔁 Generando chunks para {ia}...")

    chunk_file = os.path.join(BASE_DIR, f"{ia}_semantic_chunks.json")
    extra_chunk_file = os.path.join(BASE_DIR, f"{ia}_extra_semantic_chunks.json")

    # Borrar chunks normales y extra si existen
    for file_path in [chunk_file, extra_chunk_file]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"🗑️ Borrado {file_path}")
            except Exception as e:
                print(f"⚠️ Error al borrar {file_path}: {e}")
        else:
            print(f"📂 No existía {file_path}")

    # Ejecutar chunk_generator.py con la IA
    result = subprocess.run(["python", SCRIPT_PATH, ia])

    if result.returncode != 0:
        print(f"❌ Error al generar chunks para {ia}")
    else:
        print(f"✅ Chunks (world + extra) generados correctamente para {ia}")
