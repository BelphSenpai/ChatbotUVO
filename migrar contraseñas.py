import json
import bcrypt
import os
from collections import OrderedDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERSONAJES_PATH = os.path.join(BASE_DIR, 'www', 'personajes.json')
FICHAS_DIR = os.path.join(BASE_DIR, 'www', 'ficha', 'personajes')

LEET_MAP = str.maketrans({
    'a': '4', 'e': '3', 'i': '1', 'o': '0', 't': '7',
    'A': '4', 'E': '3', 'I': '1', 'O': '0', 'T': '7'
})


def clave_para_cabala(cabala):
    cabala = (cabala or '').strip()
    if cabala.lower() == 'trece':
        return 'l4s 7r3c3'
    return cabala.translate(LEET_MAP).lower()


def regenerar_contraseñas():
    if not os.path.exists(PERSONAJES_PATH):
        print('No se encontró personajes.json')
        return

    if not os.path.isdir(FICHAS_DIR):
        print('No se encontró el directorio de fichas')
        return

    with open(PERSONAJES_PATH, 'r', encoding='utf-8') as f:
        personajes_actuales = json.load(f)

    personajes_nuevos = OrderedDict()
    if 'admin' in personajes_actuales:
        personajes_nuevos['admin'] = personajes_actuales['admin']

    actualizados = 0
    for filename in sorted(os.listdir(FICHAS_DIR)):
        if not filename.endswith('.json') or filename == 'admin.json':
            continue

        login = os.path.splitext(filename)[0].strip().lower()
        ruta_ficha = os.path.join(FICHAS_DIR, filename)

        with open(ruta_ficha, 'r', encoding='utf-8') as f:
            ficha = json.load(f)

        clave_plana = clave_para_cabala(ficha.get('cabala', ''))
        clave_hash = bcrypt.hashpw(clave_plana.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        base_data = personajes_actuales.get(login, {})
        personaje = {
            'clave': clave_hash,
            'rol': base_data.get('rol', 'jugador')
        }
        if 'plan' in base_data:
            personaje['plan'] = base_data['plan']

        personajes_nuevos[login] = personaje
        actualizados += 1

    with open(PERSONAJES_PATH, 'w', encoding='utf-8') as f:
        json.dump(personajes_nuevos, f, indent=2, ensure_ascii=False)

    print(f'Contraseñas regeneradas para {actualizados} personajes.')


if __name__ == '__main__':
    regenerar_contraseñas()
