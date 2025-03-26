import os
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

# Claves API

OPENAI_API_KEY = os.getenv("API_KEY")
DISCORD_TOKEN = os.getenv("TOKEN_BOT")
PERSONALITY = os.getenv("PERSONALITY")
