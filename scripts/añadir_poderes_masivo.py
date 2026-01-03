#!/usr/bin/env python3
"""
Script para añadir poderes masivamente según naturaleza, cábala o senda.
Ejecutar desde el directorio raíz del proyecto.
"""

import os
import json
import sys

# Configurar paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Importar conexión Redis
from MinervaPrimeNSE.worker import get_redis_conn

FICHAS_DIR = os.path.join(BASE_DIR, 'www', 'ficha', 'personajes')
PODERES_DIR = os.path.join(BASE_DIR, 'www', 'poderes', 'usuarios')


def _poderes_redis_key(user: str) -> str:
    return f"poderes:{(user or '').strip().lower()}"


def _redis_get_poderes(user: str) -> str:
    """Obtiene poderes de un usuario desde Redis."""
    try:
        conn = get_redis_conn()
        raw = conn.get(_poderes_redis_key(user))
        if raw is None:
            return ""
        if isinstance(raw, (bytes, bytearray)):
            return raw.decode('utf-8')
        return str(raw)
    except Exception:
        return ""


def _redis_set_poderes(user: str, contenido: str):
    """Guarda poderes de un usuario en Redis."""
    try:
        conn = get_redis_conn()
        conn.set(_poderes_redis_key(user), contenido or "")
    except Exception as e:
        print(f"Error guardando en Redis para {user}: {e}")


def _sync_poderes_file_to_redis_if_missing(user: str):
    """Sincroniza desde archivo si falta en Redis."""
    try:
        if _redis_get_poderes(user):
            return
        ruta = os.path.join(PODERES_DIR, f"{user}.txt")
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            _redis_set_poderes(user, contenido)
    except Exception:
        pass


def obtener_personajes_por_naturaleza(naturaleza):
    """Obtiene todos los personajes con una naturaleza específica."""
    personajes = []
    
    if not os.path.exists(FICHAS_DIR):
        print(f"Error: No existe {FICHAS_DIR}")
        return personajes
    
    for filename in os.listdir(FICHAS_DIR):
        if not filename.endswith('.json') or filename == 'admin.json':
            continue
        
        usuario = os.path.splitext(filename)[0]
        ruta = os.path.join(FICHAS_DIR, filename)
        
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                ficha = json.load(f)
            
            if ficha.get('naturaleza', '').strip().lower() == naturaleza.lower():
                personajes.append({
                    'usuario': usuario,
                    'nombre': ficha.get('nombre_personaje', usuario)
                })
        except Exception as e:
            print(f"Error leyendo {filename}: {e}")
    
    return personajes


def añadir_poder_a_personajes(personajes, texto_poder):
    """Añade un texto de poder al final de los poderes de cada personaje."""
    añadidos = 0
    
    for personaje in personajes:
        usuario = personaje['usuario']
        
        try:
            # Sincronizar desde archivo si falta
            _sync_poderes_file_to_redis_if_missing(usuario)
            
            # Obtener poderes actuales
            poderes_actuales = _redis_get_poderes(usuario) or ""
            
            # Añadir el nuevo poder al final
            if poderes_actuales.strip():
                nuevo_contenido = f"{poderes_actuales}\n\n{texto_poder}"
            else:
                nuevo_contenido = texto_poder
            
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
            print(f"✓ {usuario} ({personaje['nombre']})")
            
        except Exception as e:
            print(f"✗ Error en {usuario}: {e}")
    
    return añadidos


if __name__ == '__main__':
    print("=== Añadir Poderes por Naturaleza ===\n")
    
    # PODERES PARA ALFILES
    print("Añadiendo LOGOS a todos los Alfiles...")
    personajes_alfiles = obtener_personajes_por_naturaleza('Alfil')
    texto_logos = """En tu naturaleza Arcana se encuentra el invocar tu paradigma:
LOGOS- Cuando convocas el poder de tu palabra y quemas un punto de rotura todos tus aliados entraran en tu burbuja de realidad alterada que los beneficiara."""
    añadidos = añadir_poder_a_personajes(personajes_alfiles, texto_logos)
    print(f"✓ Añadido a {añadidos} Alfiles\n")
    
    # PODERES PARA CABALLOS
    print("Añadiendo LIMINAL a todos los Caballos...")
    personajes_caballos = obtener_personajes_por_naturaleza('Caballo')
    texto_liminal = """En tu naturaleza mundana se encuentra el pasar bajo el radar de Entidad y Tifón.
LIMINAL - Sin coste alguno, un grupo de 3 caballos podeis ocultar una Torre que no este en forma monstruosa y con 2 caballos podeis esconder a un Alfil."""
    añadidos = añadir_poder_a_personajes(personajes_caballos, texto_liminal)
    print(f"✓ Añadido a {añadidos} Caballos\n")
    
    # PODERES PARA TORRES
    print("Añadiendo PHYLAX a todas las Torres...")
    personajes_torres = obtener_personajes_por_naturaleza('Torre')
    texto_phylax = """En tu naturaleza monstruosa se encuentra el poder de resistir daños que matarian a otros:
PHYLAX - Liberando tu forma monstruosa puedes reducir todo el daño hecho a ti o a un aliado cercano a 0 mediante el gasto de un punto de rotura."""
    añadidos = añadir_poder_a_personajes(personajes_torres, texto_phylax)
    print(f"✓ Añadido a {añadidos} Torres\n")
    
    # FORMA MONSTRUOSA PARA TORRES
    print("Añadiendo FORMA MONSTRUOSA a todas las Torres...")
    texto_forma_monstruosa = """FORMA MONSTRUOSA - Puedes ocultar tu naturaleza monstruosa temporalmente, pero para usar tu poder necesitas liberarla y cuando no te quedan puntos de rotura esta se manifiesta sola. Mientras estes en forma monstruosa cualquier agravio hacia ti se convierte en frenesi, Puedes matar aliados sin querer, de un solo golpe si son caballos, de 3 si son torres. No puedes matar alfiles accidentalmente."""
    añadidos = añadir_poder_a_personajes(personajes_torres, texto_forma_monstruosa)
    print(f"✓ Añadido a {añadidos} Torres\n")
    
    print("=== Proceso completado ===")

