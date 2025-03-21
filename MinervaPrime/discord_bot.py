import discord
from discord.ext import commands
from config import DISCORD_TOKEN
from Minerva import modo_aprendizaje, modo_consulta, iniciar_minerva
from colorama import init, Fore, Style
import os

# Inicializar colorama (importante en Windows)
init(autoreset=True)

# Intents y configuración de comandos
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# 🚀 Minerva inicia en modo consulta por defecto
MODO_DISCORD = "consulta"

@bot.event
async def on_ready():
    print(Fore.CYAN + f'✅ Minerva conectada como {bot.user}')
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
    print(f"🤖  [Minerva] {respuesta}\n{'='*50}")

    # Limitar la longitud para Discord
    if len(respuesta) > 1900:
        respuesta = respuesta[:1900] + "…"

    await message.channel.send(respuesta)

if __name__ == "__main__":
    print("Iniciando Minerva...")

    iniciar_minerva()

    print(Fore.YELLOW +"Purgando anterior historial temporal...")

    if os.path.exists("historial_temp.json"):
        os.remove("historial_temp.json")

    print(Fore.GREEN + "Historial temporal anterior purgado.")

    print(Fore.GREEN + "Minerva lista para recibir consultas.")
    modo = "consulta"

    bot.run(DISCORD_TOKEN)
