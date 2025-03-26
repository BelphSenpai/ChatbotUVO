import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from colorama import init, Fore
from utils import get_name_ia, set_name_ia, cargar_json
from Minerva import ask

# Inicializar colorama
init(autoreset=True)
load_dotenv()

# Variables globales
name_ia = os.getenv("NAME") or get_name_ia()
MODO_DISCORD = "consulta"

# Configuración de intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(Fore.CYAN + f"✅ {name_ia} conectada como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(Fore.GREEN + f"✅ {len(synced)} comandos slash sincronizados.")
    except Exception as e:
        print(Fore.RED + f"❌ Error al sincronizar comandos: {e}")

# Comando para cambiar de IA
def ia_command(nombre, emoji):
    @bot.command(name=nombre)
    async def cambiar_ia(ctx):
        set_name_ia(nombre)
        nombre_actual = get_name_ia()
        print(Fore.CYAN + f"🔄 Cambiando a {nombre_actual.upper()}...")
        await ctx.send(f"🔄 Cambiando a **{nombre_actual.capitalize()}** {emoji}")
    return cambiar_ia

# Registrar múltiples IAs
ia_command("eidolon", "☀️")
ia_command("minerva", "🧠")
ia_command("anima", "🔮")
ia_command("hada", "✨")
ia_command("fantasma", "📚")

@bot.command(name="purge")
@commands.has_permissions(manage_messages=True)
async def purge_all(ctx):
    print("🧹 Borrando todos los mensajes posibles...")
    await ctx.send("🧹 Borrando todos los mensajes posibles...")
    deleted = await ctx.channel.purge(limit=None, check=lambda m: True, bulk=True)
    await ctx.send(f"✅ Se han eliminado {len(deleted)} mensajes.", delete_after=5)
    print(Fore.GREEN + f"✅ Se han eliminado {len(deleted)} mensajes.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    global MODO_DISCORD
    user_input = message.content.strip()

    if user_input.startswith("/"):
        await bot.process_commands(message)
        return

    print(f"\n🗣️  [{message.author}] {user_input}")

    try:
        respuesta = ask(user_input)
    except Exception as e:
        respuesta = f"[ERROR] No se pudo generar respuesta: {e}"

    print(f"🤖  {name_ia}: {respuesta}\n{'='*50}")

    if len(respuesta) > 1900:
        respuesta = respuesta[:1900] + "…"

    await message.channel.send(respuesta)

if __name__ == "__main__":
    print(Fore.GREEN + f"Iniciando {name_ia}...")
    print(Fore.GREEN + f"{name_ia} lista para recibir consultas por Discord.")
    bot.run(os.getenv("TOKEN_BOT"))