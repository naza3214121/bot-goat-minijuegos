import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ─── DOBLE PREFIX ─────────────────────────────────────────
def get_prefix(bot, message):
    return ["$", "?"]

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="$help | ¡Minijuegos!"))

async def load_extensions():
    print("Iniciando carga de extensions...")

    try:
        await bot.load_extension("cogs.truco")
        print("✅ Cog truco cargado")
    except Exception as e:
        print(f"❌ Error cargando truco: {e}")

    try:
        await bot.load_extension("cogs.preguntado")
        print("✅ Cog preguntado cargado")
    except Exception as e:
        print(f"❌ Error cargando preguntado: {e}")

    try:
        await bot.load_extension("cogs.ahorcado")
        print("✅ Cog ahorcado cargado")
    except Exception as e:
        print(f"❌ Error cargando ahorcado: {e}")

    try:
        await bot.load_extension("cogs.nunca_nunca")
        print("✅ Cog nunca_nunca cargado")
    except Exception as e:
        print(f"❌ Error cargando nunca_nunca: {e}")

    try:
        await bot.load_extension("cogs.ppt")
        print("✅ Cog ppt cargado")
    except Exception as e:
        print(f"❌ Error cargando ppt: {e}")

    try:
        await bot.load_extension("cogs.wordle")
        print("✅ Cog wordle cargado")
    except Exception as e:
        print(f"❌ Error cargando wordle: {e}")

    try:
        await bot.load_extension("cogs.scramble")
        print("✅ Cog scramble cargado")
    except Exception as e:
        print(f"❌ Error cargando scramble: {e}")

    try:
        await bot.load_extension("cogs.chinchon")
        print("✅ Cog chinchon cargado")
    except Exception as e:
        print(f"❌ Error cargando chinchon: {e}")

    try:
        await bot.load_extension("cogs.help")
        print("✅ Cog help cargado")
    except Exception as e:
        print(f"❌ Error cargando help: {e}")
    
    try:
        await bot.load_extension("cogs.sugerencias")
        print("✅ Cog sugerencias cargado")
    except Exception as e:
        print(f"❌ Error cargando sugerencias: {e}")

    print("✅ Extensions cargadas. Iniciando bot...")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())