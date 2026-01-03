#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import sys

# Configurar salida UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FICHAS_DIR = os.path.join(BASE_DIR, 'www', 'ficha', 'personajes')
PODERES_DIR = os.path.join(BASE_DIR, 'www', 'poderes', 'usuarios')
os.makedirs(PODERES_DIR, exist_ok=True)

def _get_poderes_from_file(user):
    """Lee poderes desde archivo."""
    ruta = os.path.join(PODERES_DIR, f"{user}.txt")
    if os.path.exists(ruta):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""
    return ""

def _set_poderes_to_file(user, contenido):
    """Guarda poderes en archivo."""
    ruta = os.path.join(PODERES_DIR, f"{user}.txt")
    try:
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        return True
    except Exception as e:
        print(f"Error guardando archivo {user}: {e}")
        return False

def obtener_personajes_por_naturaleza(naturaleza):
    personajes = []
    for filename in os.listdir(FICHAS_DIR):
        if not filename.endswith('.json') or filename == 'admin.json':
            continue
        usuario = os.path.splitext(filename)[0]
        try:
            with open(os.path.join(FICHAS_DIR, filename), 'r', encoding='utf-8') as f:
                ficha = json.load(f)
            if ficha.get('naturaleza', '').strip().lower() == naturaleza.lower():
                personajes.append({'usuario': usuario, 'nombre': ficha.get('nombre_personaje', usuario)})
        except Exception as e:
            print(f"Error leyendo {filename}: {e}")
    return personajes

def obtener_personajes_por_cabala(cabala):
    """Obtiene todos los personajes de una cábala específica."""
    personajes = []
    for filename in os.listdir(FICHAS_DIR):
        if not filename.endswith('.json') or filename == 'admin.json':
            continue
        usuario = os.path.splitext(filename)[0]
        try:
            with open(os.path.join(FICHAS_DIR, filename), 'r', encoding='utf-8') as f:
                ficha = json.load(f)
            ficha_cabala = ficha.get('cabala', '').strip()
            if ficha_cabala.lower() == cabala.lower():
                personajes.append({'usuario': usuario, 'nombre': ficha.get('nombre_personaje', usuario)})
        except Exception as e:
            print(f"Error leyendo {filename}: {e}")
    return personajes

def obtener_personajes_por_senda(senda):
    """Obtiene todos los personajes de una senda específica."""
    personajes = []
    for filename in os.listdir(FICHAS_DIR):
        if not filename.endswith('.json') or filename == 'admin.json':
            continue
        usuario = os.path.splitext(filename)[0]
        try:
            with open(os.path.join(FICHAS_DIR, filename), 'r', encoding='utf-8') as f:
                ficha = json.load(f)
            ficha_senda = ficha.get('senda', '').strip()
            if ficha_senda.lower() == senda.lower():
                personajes.append({'usuario': usuario, 'nombre': ficha.get('nombre_personaje', usuario)})
        except Exception as e:
            print(f"Error leyendo {filename}: {e}")
    return personajes

def añadir_poder_a_personajes(personajes, texto_poder):
    añadidos = 0
    for personaje in personajes:
        usuario = personaje['usuario']
        try:
            poderes_actuales = _get_poderes_from_file(usuario) or ""
            nuevo_contenido = f"{poderes_actuales}\n\n{texto_poder}" if poderes_actuales.strip() else texto_poder
            if _set_poderes_to_file(usuario, nuevo_contenido):
                añadidos += 1
                print(f"✓ {usuario} ({personaje['nombre']})")
        except Exception as e:
            print(f"✗ Error en {usuario}: {e}")
    return añadidos

if __name__ == '__main__':
    print("=== Añadir Poderes por Naturaleza ===\n")
    
    # ALFILES - LOGOS
    print("Añadiendo LOGOS a todos los Alfiles...")
    personajes_alfiles = obtener_personajes_por_naturaleza('Alfil')
    texto_logos = """En tu naturaleza Arcana se encuentra el invocar tu paradigma:
LOGOS- Cuando convocas el poder de tu palabra y quemas un punto de rotura todos tus aliados entraran en tu burbuja de realidad alterada que los beneficiara."""
    añadidos = añadir_poder_a_personajes(personajes_alfiles, texto_logos)
    print(f"✓ Añadido a {añadidos} Alfiles\n")
    
    # CABALLOS - LIMINAL
    print("Añadiendo LIMINAL a todos los Caballos...")
    personajes_caballos = obtener_personajes_por_naturaleza('Caballo')
    texto_liminal = """En tu naturaleza mundana se encuentra el pasar bajo el radar de Entidad y Tifón.
LIMINAL - Sin coste alguno, un grupo de 3 caballos podeis ocultar una Torre que no este en forma monstruosa y con 2 caballos podeis esconder a un Alfil."""
    añadidos = añadir_poder_a_personajes(personajes_caballos, texto_liminal)
    print(f"✓ Añadido a {añadidos} Caballos\n")
    
    # TORRES - PHYLAX
    print("Añadiendo PHYLAX a todas las Torres...")
    personajes_torres = obtener_personajes_por_naturaleza('Torre')
    texto_phylax = """En tu naturaleza monstruosa se encuentra el poder de resistir daños que matarian a otros:
PHYLAX - Liberando tu forma monstruosa puedes reducir todo el daño hecho a ti o a un aliado cercano a 0 mediante el gasto de un punto de rotura."""
    añadidos = añadir_poder_a_personajes(personajes_torres, texto_phylax)
    print(f"✓ Añadido a {añadidos} Torres\n")
    
    # TORRES - FORMA MONSTRUOSA
    print("Añadiendo FORMA MONSTRUOSA a todas las Torres...")
    texto_forma_monstruosa = """FORMA MONSTRUOSA - Puedes ocultar tu naturaleza monstruosa temporalmente, pero para usar tu poder necesitas liberarla y cuando no te quedan puntos de rotura esta se manifiesta sola. Mientras estes en forma monstruosa cualquier agravio hacia ti se convierte en frenesi, Puedes matar aliados sin querer, de un solo golpe si son caballos, de 3 si son torres. No puedes matar alfiles accidentalmente."""
    añadidos = añadir_poder_a_personajes(personajes_torres, texto_forma_monstruosa)
    print(f"✓ Añadido a {añadidos} Torres\n")
    
    # PODERES POR CÁBALA
    print("\n=== Añadiendo Poderes por Cábala ===\n")
    
    # SOL INVICTO - RESISTIR CORRUPCIÓN
    print("Añadiendo RESISTIR CORRUPCIÓN a Sol Invicto...")
    personajes_sol_invicto = obtener_personajes_por_cabala('Sol invicto')
    texto_resistir_corrupcion = """RESISTIR CORRUPCIÓN: Los miembros del sol invicto tienen una resistencia natural a la mutación, cuando tifón intenta poseerte, tiene una dificultad extra."""
    añadidos = añadir_poder_a_personajes(personajes_sol_invicto, texto_resistir_corrupcion)
    print(f"✓ Añadido a {añadidos} miembros de Sol Invicto\n")
    
    # CONSULADO DEL MAR - CYBERESISTENCIA
    print("Añadiendo CYBERESISTENCIA a Consulado del Mar...")
    personajes_consulado = obtener_personajes_por_cabala('Consulado del Mar')
    texto_cyberresistencia = """CYBERESISTENCIA: Los miembros del Consulado del mar tienen una resistencia natural a la Cyberinfeccion, cuando nexus intenta poseerte, tiene una dificultad extra."""
    añadidos = añadir_poder_a_personajes(personajes_consulado, texto_cyberresistencia)
    print(f"✓ Añadido a {añadidos} miembros del Consulado del Mar\n")
    
    # INQUEBRANTABLES - LIMPIAR CYBERINFECCION
    print("Añadiendo LIMPIAR CYBERINFECCION a Inquebrantables...")
    personajes_inquebrantables = obtener_personajes_por_cabala('Inquebrantables')
    texto_limpiar_cyber = """LIMPIAR CYBERINFECCION: Como miembros de los inquebrantables podeis realizar un protocolo para reducir o augmentar la cyberinfeccion a otro."""
    añadidos = añadir_poder_a_personajes(personajes_inquebrantables, texto_limpiar_cyber)
    print(f"✓ Añadido a {añadidos} miembros de Inquebrantables\n")
    
    # TRECE - LIMPIAR CORRUPCIÓN
    print("Añadiendo LIMPIAR CORRUPCIÓN a Trece...")
    personajes_trece = obtener_personajes_por_cabala('Trece')
    texto_limpiar_corrupcion = """LIMPIAR CORRUPCIÓN: Como miembros de las Trece podeis realizar un ritual para reducir o augmentar la corrupción a otro."""
    añadidos = añadir_poder_a_personajes(personajes_trece, texto_limpiar_corrupcion)
    print(f"✓ Añadido a {añadidos} miembros de Trece\n")
    
    # PODERES POR SENDA
    print("\n=== Añadiendo Poderes por Senda ===\n")
    
    # SENDA ARCANO
    print("Añadiendo poderes de Senda Arcano...")
    personajes_arcano = obtener_personajes_por_senda('Arcano')
    texto_arcano = """Senda Arcana:

Puedes: Modificar la realidad a tu antojo, siendo solo opuesto por la realidad.
Ejemplo: Te desintegro para convertirte en componentes y energia magica.
Cuando te quedas sin rotura: Te mueres, o algo peor.
Como recuperar rotura: Puedes recuperar rotura consumiendo un miembro de tu cábala."""
    añadidos = añadir_poder_a_personajes(personajes_arcano, texto_arcano)
    print(f"✓ Añadido a {añadidos} personajes de Senda Arcano\n")
    
    # SENDA ASCLEPIO
    print("Añadiendo poderes de Senda Asclepio...")
    personajes_asclepio = obtener_personajes_por_senda('Asclepio')
    texto_asclepio = """Senda de Asclepio:

Puedes: Modificar fibras vivas, curar, mejorar o dañar partes de un ser vivo.
Ejemplo: Gasto un punto de rotura para curarte 1 punto de vida.
Cuando te quedas sin rotura: Interpretaras tener hambre.
Como recuperar rotura: Realizar una escena sobre alimentarse de otro, sangre, carne, aliento, etc."""
    añadidos = añadir_poder_a_personajes(personajes_asclepio, texto_asclepio)
    print(f"✓ Añadido a {añadidos} personajes de Senda Asclepio\n")
    
    # SENDA CIMOPOLEA
    print("Añadiendo poderes de Senda Cimopolea...")
    personajes_cimopolea = obtener_personajes_por_senda('Cimopolea')
    texto_cimopolea = """Senda de Cimopolea:

Puedes: Controlar las fuerzas energeticas, las percibes, acumulas y liberas.
Ejemplos: Gasto 1 punto de rotura para anular la puerta magnetica de seguridad.
Cuando te quedas sin rotura: Interpretaras con nerviosismo
Como recuperar rotura: Realizar una escena sobre imitar y comprender los movimientos de otra persona."""
    añadidos = añadir_poder_a_personajes(personajes_cimopolea, texto_cimopolea)
    print(f"✓ Añadido a {añadidos} personajes de Senda Cimopolea\n")
    
    # SENDA HEFESTO
    print("Añadiendo poderes de Senda Hefesto...")
    personajes_hefesto = obtener_personajes_por_senda('Hefesto')
    texto_hefesto = """Senda de Hefesto:

Puedes: Afectas la materia inorganica, crear, destruir o comprender estructuras
Ejemplo: Gasto 1 punto de rotura para crear un escudo capaz de aguantar impactos.
Cuando te quedas sin rotura: Interpretaras con frialdad mecanica.
Como recuperar rotura: Realizar una escena estudiando las protesis de otra persona, como funcionan sus conexiones."""
    añadidos = añadir_poder_a_personajes(personajes_hefesto, texto_hefesto)
    print(f"✓ Añadido a {añadidos} personajes de Senda Hefesto\n")
    
    # SENDA IRIS
    print("Añadiendo poderes de Senda Iris...")
    personajes_iris = obtener_personajes_por_senda('Iris')
    texto_iris = """Senda de Iris:

Puedes: Sientes los nodos que sostienen la realidad, puedes seguirlos o modificar.
Ejemplo: Gasto 1 punto de rotura para acceder a los archivos encriptados.
Cuando te quedas sin rotura:  Interpretaras desorientación.
Como recuperar rotura: Realizar una escena sobre trazar un nodo, sea fisico o digital, comprender un entorno junto a otro."""
    añadidos = añadir_poder_a_personajes(personajes_iris, texto_iris)
    print(f"✓ Añadido a {añadidos} personajes de Senda Iris\n")
    
    # SENDA KAIROS
    print("Añadiendo poderes de Senda Kairos...")
    personajes_kairos = obtener_personajes_por_senda('Kairos')
    texto_kairos = """Senda de Kairos:

Puedes: Percibir el flujo del tiempo, retroceder escasos segundos.
Ejemplo: Gasto 1 punto de rotura para haberme anticipado a esto y tener una pistola.
Cuando te quedas sin rotura: Actuaras con Lagunas de memoria.
Como recuperar rotura: Debes escuchar con suma atención un recuerdo importante de otra persona."""
    añadidos = añadir_poder_a_personajes(personajes_kairos, texto_kairos)
    print(f"✓ Añadido a {añadidos} personajes de Senda Kairos\n")
    
    # SENDA MORFEO
    print("Añadiendo poderes de Senda Morfeo...")
    personajes_morfeo = obtener_personajes_por_senda('Morfeo')
    texto_morfeo = """Senda de Morfeo:

Puedes: Puedes modificar las mentes del entorno que tienen su atención en ti.
Ejemplo: Gasto 1 punto de rotura para que desorietar a los legionarios.
Cuando te quedas sin rotura: Actuaras con Dramatismo
Como recuperar rotura: Escucharas y animaras los sueños de otra persona."""
    añadidos = añadir_poder_a_personajes(personajes_morfeo, texto_morfeo)
    print(f"✓ Añadido a {añadidos} personajes de Senda Morfeo\n")
    
    # SENDA NEMESIS
    print("Añadiendo poderes de Senda Nemesis...")
    personajes_nemesis = obtener_personajes_por_senda('Nemesis')
    texto_nemesis = """Senda de Nemesis:

Puedes: Percibes la entropia que lo degrada y dirige todo, puedes usarla.
Ejemplo: Gasto un punto de rotura para ver el punto debil en su armadura.
Cuando te quedas sin rotura: Actuaras con Rabia.
Como recuperar rotura: Escucharas la historia de algo importante, sea un objeto, una persona, un sitio, perdido para siempre."""
    añadidos = añadir_poder_a_personajes(personajes_nemesis, texto_nemesis)
    print(f"✓ Añadido a {añadidos} personajes de Senda Nemesis\n")
    
    # SENDA TANATHOS
    print("Añadiendo poderes de Senda Tanathos...")
    personajes_tanathos = obtener_personajes_por_senda('Tanathos')
    texto_tanathos = """Senda de Tanathos:

Puedes: Puedes pactar con espiritus a traves de tu pacto previo.
Ejemplo: Gasto 1 punto de rotura para convocar un espiritu que me ayude.
Cuando te quedas sin rotura: Actuaras como el espiritu que te acompaña
Como recuperar rotura: Tu espiritu realizara un chiminaje, un trato, con alguien, a cambio de devolverte."""
    añadidos = añadir_poder_a_personajes(personajes_tanathos, texto_tanathos)
    print(f"✓ Añadido a {añadidos} personajes de Senda Tanathos\n")
    
    # SENDA HELIOS
    print("Añadiendo poderes de Senda Helios...")
    personajes_helios = obtener_personajes_por_senda('Helios')
    texto_helios = """Senda de Helios:

Puedes: La fe en tus convicciones de imbuye a ti y a lo que te rodea.
Ejemplo: Gasto 1 punto de rotura para nutrir de fé mi espada.
Cuando te quedas sin rotura: Actuaras con tristeza.
Como recuperar rotura: Realizaras una oracion, bendicion o ritual a otra persona en honor a tu compromiso y conviccion."""
    añadidos = añadir_poder_a_personajes(personajes_helios, texto_helios)
    print(f"✓ Añadido a {añadidos} personajes de Senda Helios\n")
    
    print("=== Proceso completado ===")

