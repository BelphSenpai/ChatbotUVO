import discord
from discord.ext import commands
from config import DISCORD_TOKEN
from Minerva import modo_aprendizaje, modo_consulta, iniciar_minerva
from colorama import init, Fore, Style
import os
from sklearn.preprocessing import normalize
from dotenv import load_dotenv
from utils import get_name_ia, set_name_ia

# Inicializar colorama (importante en Windows)
init(autoreset=True)

# Intents y configuración de comandos
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# 🚀 Minerva inicia en modo consulta por defecto
MODO_DISCORD = "consulta"

#cargo las variables de entorno

load_dotenv()

name_ia = os.getenv("NAME")

@bot.event
async def on_ready():
    print(Fore.CYAN + f'✅ {name_ia} conectada como {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(Fore.GREEN + f'Se han sincronizado {len(synced)} comandos slash.')
    except Exception as e:
        print(Fore.RED + f'Error al sincronizar: {e}')

@bot.command(name="aprendizaje")
async def cambiar_modo_aprendizaje(ctx):
    global MODO_DISCORD
    MODO_DISCORD = "aprendizaje"    
    print(Fore.CYAN + "🔄 Modo cambiado a APRENDIZAJE")
    await ctx.send("🔄 Modo cambiado a **aprendizaje**.")

@bot.command(name="eidolon")
async def cambiar_ia_eidolon(ctx):
    set_name_ia("eidolon")
    nombre = get_name_ia()
    print(Fore.CYAN + f"🔄 Cambiando a {nombre.upper()}...")
    await ctx.send(f"🔄 Cambia  ndo a **{nombre.capitalize()}**...")
    iniciar_minerva(nombre)
    print(Fore.CYAN + f"🔄 Cambiado a {nombre.upper()}☀️")
    await ctx.send(f"🔄 Cambiado a **{nombre.capitalize()}**☀️.")

@bot.command(name="minerva")
async def cambiar_ia_minerva(ctx):
    set_name_ia("minerva")
    nombre = get_name_ia()
    print(Fore.CYAN + f"🔄 Cambiando a {nombre.upper()}...")
    await ctx.send(f"🔄 Cambiando a **{nombre.capitalize()}**...")
    iniciar_minerva(nombre)
    print(Fore.CYAN + f"🔄 Cambiado a {nombre.upper()}🧠")
    await ctx.send(f"🔄 Cambiado a **{nombre.capitalize()}**🧠.")


@bot.command(name="anima")
async def cambiar_ia_anima(ctx):
    set_name_ia("anima")
    nombre = get_name_ia()
    print(Fore.CYAN + f"🔄 Cambiando a {nombre.upper()}...")
    await ctx.send(f"🔄 Cambiando a **{nombre.capitalize()}**...")
    iniciar_minerva(nombre)
    print(Fore.CYAN + f"🔄 Cambiado a {nombre.upper()}🔮")
    await ctx.send(f"🔄 Cambiado a **{nombre.capitalize()}**🔮.")

@bot.command(name="hada")
async def cambiar_ia_hada(ctx):
    set_name_ia("hada")
    nombre = get_name_ia()
    print(Fore.MAGENTA + f"⚡ Cambiando a {nombre.upper()}...")
    await ctx.send(f"⚡ Cambiando a **{nombre.capitalize()}**...")
    iniciar_minerva(nombre)
    print(Fore.MAGENTA + f"⚡ Cambiado a {nombre.upper()} ✨")
    await ctx.send(f"⚡ Cambiado a **{nombre.capitalize()}** ✨")

@bot.command(name="fantasma")
async def cambiar_ia_fantasma(ctx):
    set_name_ia("fantasma")
    nombre = get_name_ia()
    print(Fore.BLUE + f"📚 Cambiando a {nombre.upper()}...")
    await ctx.send(f"📚 Cambiando a **{nombre.capitalize()}**...")
    iniciar_minerva(nombre)
    print(Fore.BLUE + f"📚 Cambiado a {nombre.upper()} 🧠")
    await ctx.send(f"📚 Cambiado a **{nombre.capitalize()}** 🧠")

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge_all(ctx):
    print("🧹 Borrando todos los mensajes posibles...")
    await ctx.send("🧹 Borrando todos los mensajes posibles...")

    def check(msg):
        return True  # Borra todos los mensajes posibles

    deleted = await ctx.channel.purge(limit=None, check=check, bulk=True)
    await ctx.send(f"✅ Se han eliminado {len(deleted)} mensajes.", delete_after=5)
    print(Fore.GREEN + f"✅ Se han eliminado {len(deleted)} mensajes.", delete_after=5)

@bot.command(name="consulta")
async def cambiar_modo_consulta(ctx):
    global MODO_DISCORD
    MODO_DISCORD = "consulta"
    print(Fore.CYAN +"🔄 Modo cambiado a CONSULTA")
    await ctx.send("🔄 Modo cambiado a **consulta**.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    global MODO_DISCORD
    user_input = message.content.strip()

    # Ignorar comandos para evitar bucles infinitos
    if user_input.startswith("/"):
        await bot.process_commands(message)
        return

    print(f"\n🗣️  [{message.author}] {user_input}")  # Log del mensaje recibido

    # Generar respuesta según el modo
    respuesta = modo_aprendizaje(user_input) if MODO_DISCORD == "aprendizaje" else modo_consulta(user_input)

    # Log de la respuesta en terminal
    print(f"🤖  {name_ia}: {respuesta}\n{'='*50}")

    # Limitar la longitud para Discord
    if len(respuesta) > 1900:
        respuesta = respuesta[:1900] + "…"

    await message.channel.send(respuesta)

if __name__ == "__main__":
    
    print("Iniciando "+name_ia+"...")

    iniciar_minerva()

    print(Fore.GREEN + "Historial temporal anterior purgado.")

    print(Fore.GREEN + f"{name_ia} lista para recibir consultas.")
    modo = "consulta"

    bot.run(DISCORD_TOKEN)
