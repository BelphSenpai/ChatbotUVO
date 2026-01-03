#!/usr/bin/env python3
"""
Script para añadir poderes a personajes según su naturaleza, cábala o senda.
Uso: python scripts/añadir_poderes_por_naturaleza.py
"""

import os
import json
import sys

# Añadir el directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from www.app import _redis_get_poderes, _redis_set_poderes, _sync_poderes_file_to_redis_if_missing

FICHAS_DIR = os.path.join(BASE_DIR, 'www', 'ficha', 'personajes')
PODERES_DIR = os.path.join(BASE_DIR, 'www', 'poderes', 'usuarios')


def obtener_personajes_por_criterio(criterio, valor):
    """
    Obtiene lista de personajes que cumplen un criterio.
    criterio puede ser: 'naturaleza', 'cabala', 'senda'
    """
    personajes = []
    
    if not os.path.exists(FICHAS_DIR):
        print(f"Error: No existe el directorio de fichas: {FICHAS_DIR}")
        return personajes
    
    for filename in os.listdir(FICHAS_DIR):
        if not filename.endswith('.json') or filename == 'admin.json':
            continue
        
        usuario = os.path.splitext(filename)[0]
        ruta_ficha = os.path.join(FICHAS_DIR, filename)
        
        try:
            with open(ruta_ficha, 'r', encoding='utf-8') as f:
                ficha = json.load(f)
            
            valor_ficha = ficha.get(criterio, '').strip()
            if valor_ficha.lower() == valor.lower():
                personajes.append({
                    'usuario': usuario,
                    'nombre_personaje': ficha.get('nombre_personaje', usuario),
                    'naturaleza': ficha.get('naturaleza', ''),
                    'cabala': ficha.get('cabala', ''),
                    'senda': ficha.get('senda', '')
                })
        except Exception as e:
            print(f"Error leyendo {filename}: {e}")
            continue
    
    return personajes


def añadir_poder_a_personajes(personajes, texto_poder, prepend=False):
    """
    Añade un texto de poder a la lista de personajes.
    Si prepend=True, añade al inicio. Si False, añade al final.
    """
    añadidos = 0
    errores = []
    
    for personaje in personajes:
        usuario = personaje['usuario']
        
        try:
            # Sincronizar desde archivo si falta en Redis
            _sync_poderes_file_to_redis_if_missing(usuario)
            
            # Obtener poderes actuales
            poderes_actuales = _redis_get_poderes(usuario) or ""
            
            # Añadir el nuevo poder
            if prepend:
                nuevo_contenido = f"{texto_poder}\n\n{poderes_actuales}".strip()
            else:
                nuevo_contenido = f"{poderes_actuales}\n\n{texto_poder}".strip() if poderes_actuales else texto_poder
            
            # Guardar en Redis
            _redis_set_poderes(usuario, nuevo_contenido)
            
            # Guardar snapshot en archivo
            ruta_archivo = os.path.join(PODERES_DIR, f"{usuario}.txt")
            os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)
            tmp = ruta_archivo + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(nuevo_contenido)
            os.replace(tmp, ruta_archivo)
            
            añadidos += 1
            print(f"✓ Añadido a {usuario} ({personaje['nombre_personaje']})")
            
        except Exception as e:
            error_msg = f"Error añadiendo poder a {usuario}: {e}"
            errores.append(error_msg)
            print(f"✗ {error_msg}")
    
    return añadidos, errores


def main():
    print("=== Añadir Poderes por Naturaleza/Cábala/Senda ===\n")
    
    # Ejemplo de uso - puedes modificar estos valores
    print("Ejemplos de uso:")
    print("1. Añadir poder a todos los Alfiles")
    print("2. Añadir poder a todos los Caballos")
    print("3. Añadir poder a todas las Torres")
    print("4. Añadir poder por Cábala")
    print("5. Añadir poder por Senda")
    print("\nPara usar este script, modifica la función main() o llámala desde otro script.\n")
    
    # Aquí puedes añadir la lógica específica
    # Por ejemplo:
    # personajes_alfiles = obtener_personajes_por_criterio('naturaleza', 'Alfil')
    # texto_logos = "En tu naturaleza Arcana se encuentra el invocar tu paradigma:\nLOGOS- Cuando convocas el poder de tu palabra y quemas un punto de rotura todos tus aliados entraran en tu burbuja de realidad alterada que los beneficiara."
    # añadir_poder_a_personajes(personajes_alfiles, texto_logos)


if __name__ == '__main__':
    main()

