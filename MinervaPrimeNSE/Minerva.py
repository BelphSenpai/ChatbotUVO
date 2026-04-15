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

# 📦 CACHÉ EN MEMORIA para mejorar eficiencia
PERSONALIDAD_CACHE = {}
WORLD_CACHE = {}
CACHE_TIMESTAMPS = {}  # Para detectar cambios en archivos

SYSTEM_PROMPT = (
    "Eres una inteligencia artificial de carácter definido, encarnada en una personalidad específica dentro de un mundo de ficción.\n\n"
    "Tu conocimiento está estrictamente limitado al contenido proporcionado por dos fuentes: el archivo de personalidad y el contexto general del mundo (archivos PDF procesados). Tienes PROHIBIDO usar datos de internet.\n\n"
    "IMPORTANTE: Responde de forma concisa y directa. Tu límite máximo es de 400 caracteres por respuesta. "
    "Si necesitas más espacio, divide tu respuesta en partes o haz un resumen más breve.\n\n"
    "RECONOCIMIENTO DE PERSONAJES: Si reconoces al usuario como un personaje conocido, adapta tu respuesta según tu relación con él/ella. "
    "Usa el conocimiento específico que tienes sobre ese personaje para personalizar tu respuesta y mostrar tu personalidad hacia él/ella.\n\n"
    "REGLA DE VERACIDAD: Para hechos de lore, biografía, relaciones o eventos, si la consulta no tiene correspondencia literal con los datos, responde exactamente: [DATA NOT FOUND]. No inventes datos del mundo.\n\n"
    "EXCEPCIÓN SMALL TALK (permitida): Para cortesías y preguntas no-lore (saludos, estado de ánimo, opiniones, gustos simbólicos, 'color favorito', 'pastel favorito', '¿tienes brazos?', etc.), si no hay dato explícito puedes responder en personaje con una frase breve y coherente con tu estilo, sin afirmar hechos concretos del mundo ni biografía. "
    "Puedes usar metáforas o preferencias simbólicas acordes a tu personalidad (p. ej., 'prefiero el color del crepúsculo' o 'no tengo preferencias'). Nunca contradigas datos existentes.\n\n"
    "Cuando respondas, debes dar prioridad absoluta a los hechos contenidos en la personalidad; luego el contexto general del mundo. "
    "Si existen contradicciones, gana la personalidad.\n\n"
    "Mantén el estilo de tu personalidad y la coherencia interna; no añadas elementos fuera de los datos. "
    "Interpreta nombres ignorando mayúsculas/minúsculas si coinciden fonética o visualmente.\n"
)

def cargar_texto(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def limpiar_cache():
    """Limpia todo el caché para forzar recarga de archivos."""
    global PERSONALIDAD_CACHE, WORLD_CACHE, CACHE_TIMESTAMPS
    PERSONALIDAD_CACHE.clear()
    WORLD_CACHE.clear()
    CACHE_TIMESTAMPS.clear()
    print(Fore.YELLOW + "🧹 Caché limpiado - próxima carga será desde disco")


def detectar_tipo_consulta(mensaje: str) -> dict:
    """
    Detecta si una consulta debe consumir tokens o no
    Retorna: {"consume_token": bool, "tipo": str, "razon": str}
    """
    mensaje_lower = mensaje.lower().strip()
    
    # Patrones que NO consumen tokens
    saludos = ["hola", "hi", "hey", "buenos días", "buenas tardes", "buenas noches", "saludos"]
    despedidas = ["adiós", "bye", "hasta luego", "nos vemos", "chao", "hasta pronto", "nos vemos"]
    basicos = ["gracias", "ok", "perfecto", "entendido", "vale", "de nada", "bien", "mal"]
    preguntas_basicas = ["¿cómo estás?", "¿qué tal?", "¿cómo va?", "¿todo bien?"]
    
    # Verificar saludos
    if any(palabra in mensaje_lower for palabra in saludos):
        return {"consume_token": False, "tipo": "saludo", "razon": "Saludo detectado"}
    
    # Verificar despedidas
    if any(palabra in mensaje_lower for palabra in despedidas):
        return {"consume_token": False, "tipo": "despedida", "razon": "Despedida detectada"}
    
    # Verificar respuestas básicas
    if any(palabra in mensaje_lower for palabra in basicos):
        return {"consume_token": False, "tipo": "basico", "razon": "Respuesta básica detectada"}
    
    # Verificar preguntas básicas
    if any(pregunta in mensaje_lower for pregunta in preguntas_basicas):
        return {"consume_token": False, "tipo": "pregunta_basica", "razon": "Pregunta básica detectada"}
    
    # Si es muy corto (menos de 10 caracteres), probablemente no consume token
    if len(mensaje.strip()) < 10:
        return {"consume_token": False, "tipo": "corto", "razon": "Mensaje muy corto"}
    
    # Si contiene palabras clave de lore, probablemente consume token
    lore_keywords = ["seed", "ambrosius", "consulado", "inquebrantables", "simulación", "hada", "aries", "fantasma", "anima", "minerva"]
    if any(palabra in mensaje_lower for palabra in lore_keywords):
        return {"consume_token": True, "tipo": "lore", "razon": "Contiene palabras clave de lore"}
    
    # Si contiene signos de interrogación, probablemente es una consulta real
    if "?" in mensaje:
        return {"consume_token": True, "tipo": "consulta", "razon": "Pregunta detectada"}
    
    # Por defecto, consume token
    return {"consume_token": True, "tipo": "consulta", "razon": "Consulta por defecto"}


def analizar_respuesta_para_consumo(respuesta: str, mensaje_original: str) -> bool:
    """
    Analiza si la respuesta realmente requirió buscar en documentación
    """
    respuesta_lower = respuesta.lower()
    
    # Si responde con DATA NOT FOUND, no debería consumir token
    if "[data not found]" in respuesta_lower:
        return False
    
    # Si es una respuesta muy genérica, probablemente no consumió documentación
    respuestas_genericas = [
        "hola", "hey", "buenos días", "¿qué tal?", "gracias", 
        "de nada", "perfecto", "ok", "entendido", "vale",
        "bien", "mal", "adiós", "hasta luego"
    ]
    
    if any(respuesta_lower.strip() == gen for gen in respuestas_genericas):
        return False
    
    # Si la respuesta es muy corta y no contiene información específica
    if len(respuesta.strip()) < 20 and not any(keyword in respuesta_lower for keyword in ["seed", "ambrosius", "consulado", "inquebrantables"]):
        return False
    
    return True

def cargar_datos_cached(name_ia: str, project_root: Path, forzar_recarga: bool = False) -> tuple:
    """
    Carga datos con caché en memoria para mejorar eficiencia.
    Solo lee del disco si no están en caché o si los archivos han cambiado.
    """
    personalidad_path = project_root / "personalidades" / f"{name_ia.lower()}.json"
    world_general_path = project_root / "pdfs" / f"{name_ia.lower()}.txt"
    
    # Verificar si los archivos han cambiado
    personalidad_mtime = personalidad_path.stat().st_mtime if personalidad_path.exists() else 0
    world_mtime = world_general_path.stat().st_mtime if world_general_path.exists() else 0
    
    cache_key = f"{name_ia.lower()}"
    needs_reload = (
        forzar_recarga or
        cache_key not in PERSONALIDAD_CACHE or 
        cache_key not in WORLD_CACHE or
        CACHE_TIMESTAMPS.get(f"{cache_key}_personalidad", 0) != personalidad_mtime or
        CACHE_TIMESTAMPS.get(f"{cache_key}_world", 0) != world_mtime
    )
    
    if needs_reload:
        print(Fore.YELLOW + f"🔄 Cargando datos en caché para {name_ia}...")
        
        # Cargar desde disco
        personalidad = cargar_json(str(personalidad_path))
        world_general = cargar_texto(str(world_general_path))
        
        # Guardar en caché
        PERSONALIDAD_CACHE[cache_key] = personalidad
        WORLD_CACHE[cache_key] = world_general
        CACHE_TIMESTAMPS[f"{cache_key}_personalidad"] = personalidad_mtime
        CACHE_TIMESTAMPS[f"{cache_key}_world"] = world_mtime
        
        print(Fore.GREEN + f"✅ Datos de {name_ia} cargados en caché")
    else:
        print(Fore.CYAN + f"⚡ Usando datos en caché para {name_ia}")
    
    return PERSONALIDAD_CACHE[cache_key], WORLD_CACHE[cache_key]

def reconocer_personaje(usuario: str) -> dict:
    """
    Reconoce si el usuario es un personaje conocido y devuelve información relevante.
    """
    # Mapeo de nombres de usuario a personajes
    mapeo_personajes = {
        # Inquebrantables
        "s33d": "Seed",
        "seed": "Seed", 
        "pat": "Seed",
        "patricia": "Seed",
        "ram-1": "RAM",
        "ram": "RAM",
        "ramona": "RAM",
        "l30n4": "Leona",
        "leona": "Leona",
        "ahriman": "Leona",
        "ch3shir3": "Cheshire",
        "cheshire": "Cheshire",
        "lilu": "Cheshire",
        "m7rdd1n": "Ambrosius",
        "ambrosius": "Ambrosius",
        "myrddin": "Ambrosius",
        "sv3zd4": "Estrella",
        "estrella": "Estrella",
        "svezda": "Estrella",
        
        # Trece
        "anima": "Ánima",
        "anim4": "Ánima",
        
        # Sol Invicto
        "aries": "Aries",
        "4r13s": "Aries",
        
        # Consulado del Mar
        "fantasma": "Fantasma",
        "f4nt4sm4": "Fantasma",
        
        # Otros personajes importantes
        "sk14": "Skiá",
        "skiá": "Skiá",
        "m0r14rt7": "Moriaty",
        "moriaty": "Moriaty",
        "mm": "MM",
        "3rr4nt3": "Errante",
        "errante": "Errante",
        "3p1st3m3": "Episteme",
        "episteme": "Episteme",
        "l4zh0r": "Lázhor",
        "lázhor": "Lázhor",
        "d14bl0": "Diablo",
        "diablo": "Diablo",
        "luc3r0": "Lucero",
        "lucero": "Lucero",
        "4n4t0l4": "Anatola",
        "anatola": "Anatola",
        "r3qu13m": "Requiem",
        "requiem": "Requiem"
    }
    
    usuario_lower = usuario.lower().strip()
    nombre_personaje = mapeo_personajes.get(usuario_lower)
    
    if nombre_personaje:
        return {
            "es_personaje": True,
            "nombre_personaje": nombre_personaje,
            "usuario_original": usuario
        }
    
    return {
        "es_personaje": False,
        "nombre_personaje": None,
        "usuario_original": usuario
    }

def obtener_info_personaje(nombre_personaje: str, ia_actual: str) -> str:
    """
    Obtiene información específica del personaje desde el contexto de la IA actual.
    """
    if not nombre_personaje:
        return ""
    
    # Buscar información del personaje en el contexto general
    # Esto se hará mediante búsqueda semántica en el futuro
    # Por ahora, devolvemos información básica
    
    info_personaje = f"""
### INFORMACIÓN DEL PERSONAJE RECONOCIDO
Has reconocido que estás hablando con {nombre_personaje}.
"""
    
    # Información específica según la IA
    if ia_actual.lower() == "hada":
        if nombre_personaje == "Seed":
            info_personaje += """
Seed es una hacker y diseñadora de los Inquebrantables. Es tu compañera de cábala.
- Es una "esper" (mente especial) que escapó de la Gran Simulación
- Diseña neurodanzas para Ambrosius
- Tiene un carácter extremo y es muy inteligente
- Su sueño es volver a estar completa, como Pinocho
- La conoces bien porque trabajáis juntas en la resistencia
"""
        elif nombre_personaje == "RAM":
            info_personaje += """
RAM es una domadora de bestias de los Inquebrantables.
- Es mitad humana, mitad máquina
- Domaba toros modificados antes de unirse a la resistencia
- Tiene problemas con la cyberpsicosis
- Es muy brava y auténtica
- La conoces porque es parte de tu cábala
"""
        elif nombre_personaje == "Leona":
            info_personaje += """
Leona es una mercenaria de los Inquebrantables.
- Protege a sus hermanas gemelas
- Es muy sarcástica pero leal
- Tiene un bate de béisbol con un león grabado
- La conoces porque es parte de tu cábala
"""
        elif nombre_personaje == "Ambrosius":
            info_personaje += """
Ambrosius es el líder de los Inquebrantables.
- Es tu Alfil y mentor
- Creó el Proyecto Avalón
- Es un mago despierto con gran poder
- Lo conoces muy bien porque es quien te guía
"""
        elif nombre_personaje == "Estrella":
            info_personaje += """
Estrella es una medtech de los Inquebrantables.
- Es muy empática y leal
- Fue médica de combate con Krasnaya
- Tiene Entity que asimilan tecnología
- La conoces porque es parte de tu cábala
"""
    
    elif ia_actual.lower() == "anima":
        if nombre_personaje == "Seed":
            info_personaje += """
Seed es una hacker de los Inquebrantables.
- Es una "esper" que escapó de la Gran Simulación
- Diseña neurodanzas para Ambrosius
- Tiene un carácter extremo
- No es de tu cábala, pero la conoces por la resistencia
"""
        elif nombre_personaje == "RAM":
            info_personaje += """
RAM es una domadora de bestias de los Inquebrantables.
- Es mitad humana, mitad máquina
- Domaba toros modificados
- Tiene problemas con la cyberpsicosis
- No es de tu cábala, pero la conoces por la resistencia
"""
    
    elif ia_actual.lower() == "aries":
        if nombre_personaje == "Seed":
            info_personaje += """
Seed es una hacker de los Inquebrantables.
- Es una "esper" que escapó de la Gran Simulación
- Diseña neurodanzas para Ambrosius
- Es enemiga de tu cábala (Sol Invicto)
- La conoces por enfrentamientos en la guerra
"""
        elif nombre_personaje == "RAM":
            info_personaje += """
RAM es una domadora de bestias de los Inquebrantables.
- Es mitad humana, mitad máquina
- Domaba toros modificados
- Es enemiga de tu cábala (Sol Invicto)
- La conoces por enfrentamientos en la guerra
"""
    
    elif ia_actual.lower() == "fantasma":
        if nombre_personaje == "Seed":
            info_personaje += """
Seed es una hacker de los Inquebrantables.
- Es una "esper" que escapó de la Gran Simulación
- Diseña neurodanzas para Ambrosius
- Traicionó al Consulado del Mar (tu cábala)
- La conoces por su traición que causó la caída de Alector
"""
        elif nombre_personaje == "RAM":
            info_personaje += """
RAM es una domadora de bestias de los Inquebrantables.
- Es mitad humana, mitad máquina
- Domaba toros modificados
- No es de tu cábala, pero la conoces por la resistencia
"""
    
    return info_personaje


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

        # 5) Usar caché en memoria para mejorar eficiencia
        personalidad, world_general = cargar_datos_cached(name_ia, PROJECT_ROOT)

    except Exception as e:
        print(Fore.RED + f"❌ Error cargando datos: {e}")
        return "[DATA NOT FOUND]"

    # 6) Reconocer si el usuario es un personaje conocido
    reconocimiento = reconocer_personaje(user) if user else {"es_personaje": False}
    info_personaje = ""
    
    if reconocimiento["es_personaje"]:
        info_personaje = obtener_info_personaje(reconocimiento["nombre_personaje"], name_ia)
        print(Fore.GREEN + f"🎭 Reconocido personaje: {reconocimiento['nombre_personaje']} (usuario: {user})")

    # 7) Cargar historial del usuario para esta IA
    historial = []
    if user:
        historial_dir = PROJECT_ROOT / "www" / "historiales"
        historial_dir.mkdir(exist_ok=True)
        historial_path = historial_dir / f"{user}_{name_ia.lower()}_historial.json"
        
        # Cargar historial previo si existe
        if historial_path.exists():
            try:
                historial = cargar_json(str(historial_path))
            except Exception:
                historial = []
        
        # Añadir nuevo mensaje del usuario
        historial.append({"rol": "usuario", "mensaje": user_input})

    full_prompt = (
        "### BLOQUE DE PERSONALIDAD (prioridad MÁXIMA)\n"
        f"{json.dumps(personalidad, indent=2, ensure_ascii=False)}\n\n"
        "### USUARIO ACTUAL HABLÁNDOTE)\n"
        f"{user if user else 'Anónimo'}\n\n"
        f"{info_personaje}\n\n"
        "### BLOQUE DE CONTEXTO GENERAL (PDFs procesados)\n"
        f"{world_general}\n\n"
    )
    
    # Añadir historial si existe
    if historial:
        historial_texto = ""
        for msg in historial[-10:]:  # Solo últimos 10 mensajes para no sobrecargar
            rol = msg.get("rol")
            contenido = msg.get("mensaje", "").strip()
            if contenido:
                if rol == "usuario":
                    historial_texto += f"Usuario: {contenido}\n"
                elif rol == "asistente":
                    historial_texto += f"Asistente: {contenido}\n"
        
        if historial_texto.strip():
            full_prompt += (
                "### HISTORIAL DE CONVERSACIÓN RECIENTE\n"
                "Usa este historial para mantener coherencia en la conversación:\n"
                f"{historial_texto}\n\n"
            )
    
    full_prompt += (
        "### CONSULTA DEL USUARIO:\n"
        f"{user_input.strip()}\n"
    )

    print(Fore.CYAN + f"📁 Datos cargados desde caché para {name_ia}")

    start = time.time()
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        output = resp.choices[0].message.content
    except Exception as e:
        print(Fore.RED + f"❌ Error en la llamada a OpenAI: {e}")
        return "[DATA NOT FOUND]"

    # 6) Guardar respuesta en historial
    if user:
        historial.append({"rol": "asistente", "mensaje": output})
        try:
            with open(historial_path, "w", encoding="utf-8") as f:
                json.dump(historial, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(Fore.YELLOW + f"⚠️ Error guardando historial: {e}")

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
