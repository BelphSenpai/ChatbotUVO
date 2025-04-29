import json
import bcrypt
import os

# Ajusta esta ruta si es necesario
PERSONAJES_PATH = os.path.join('www', 'personajes.json')

def migrar_contraseñas():
    if not os.path.exists(PERSONAJES_PATH):
        print("No se encontró personajes.json")
        return

    with open(PERSONAJES_PATH, 'r', encoding='utf-8') as f:
        personajes = json.load(f)

    actualizados = 0

    for nombre, datos in personajes.items():
        clave = datos.get('clave', '')
        # Si la clave no empieza por $2b$, asumimos que no está hasheada
        if not clave.startswith('$2b$'):
            clave_bytes = clave.encode('utf-8')
            hash_nuevo = bcrypt.hashpw(clave_bytes, bcrypt.gensalt()).decode('utf-8')
            personajes[nombre]['clave'] = hash_nuevo
            actualizados += 1

    with open(PERSONAJES_PATH, 'w', encoding='utf-8') as f:
        json.dump(personajes, f, indent=2, ensure_ascii=False)

    print(f"Migración completada. {actualizados} contraseñas hasheadas.")

if __name__ == '__main__':
    migrar_contraseñas()
