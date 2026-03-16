import discord
from discord.ext import commands
import random
import asyncio
import aiohttp
import re

COLOR = discord.Color.teal()
COLOR_ERROR = discord.Color.red()
COLOR_WIN = discord.Color.green()

PALABRAS_URL = "https://raw.githubusercontent.com/ManiacDC/TypingAid/master/Wordlists/Wordlist%20Spanish.txt"
PALABRAS_CACHE = []

FALLBACK = [
    "computadora", "dinosaurio", "mariposa", "chocolate", "aventura",
    "telescopio", "biblioteca", "universo", "guitarra", "filosofia",
    "volcán", "cascada", "laberinto", "cocodrilo", "submarino",
    "fotografia", "laboratorio", "hamburguesa", "calendario", "revolucion",
]

async def cargar_palabras_scramble():
    global PALABRAS_CACHE
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PALABRAS_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    texto = await resp.text(encoding="utf-8", errors="ignore")
                    todas = texto.strip().splitlines()
                    PALABRAS_CACHE = [
                        p.strip().lower() for p in todas
                        if p.strip().isalpha() and 5 <= len(p.strip()) <= 12
                    ]
                    print(f"✅ Scramble: {len(PALABRAS_CACHE)} palabras cargadas")
                else:
                    PALABRAS_CACHE = FALLBACK
    except Exception as e:
        print(f"⚠️ Scramble: {e}")
        PALABRAS_CACHE = FALLBACK

def mezclar_palabra(palabra):
    letras = list(palabra)
    mezclada = letras.copy()
    intentos = 0
    while mezclada == letras and intentos < 20:
        random.shuffle(mezclada)
        intentos += 1
    return "".join(mezclada)

def normalizar(s):
    reemplazos = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ü':'u','Á':'a','É':'e','Í':'i','Ó':'o','Ú':'u'}
    return ''.join(reemplazos.get(c, c) for c in s).lower().strip()

# partida global por canal: {canal_id: {palabra, mezclada, activa}}
scrambles_activos: dict = {}

class Scramble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not PALABRAS_CACHE:
            await cargar_palabras_scramble()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        canal_id = message.channel.id
        if canal_id not in scrambles_activos:
            return
        datos = scrambles_activos[canal_id]
        if not datos["activa"]:
            return
        intento = message.content.strip()
        if normalizar(intento) == normalizar(datos["palabra"]):
            datos["activa"] = False
            del scrambles_activos[canal_id]
            embed = discord.Embed(
                title="🎉 ¡Correcto!",
                description=f"**{message.author.display_name}** adivinó la palabra: **{datos['palabra'].upper()}**",
                color=COLOR_WIN
            )
            await message.channel.send(embed=embed)

    @commands.group(name="scramble", aliases=["scr"], invoke_without_command=True)
    async def scramble(self, ctx):
        embed = discord.Embed(title="🔀 Scramble — Ayuda", color=COLOR)
        embed.add_field(name="$scramble jugar", value="Mezcla una palabra al azar y el primero en adivinarla gana.", inline=False)
        embed.add_field(name="$scramble terminar", value="Termina el scramble activo (solo admins).", inline=False)
        embed.add_field(name="💡 Cómo jugar", value="El bot muestra las letras mezcladas. Escribí la palabra en el chat para ganar.\n¡Sin sala, global para todos en el canal!", inline=False)
        await ctx.send(embed=embed)

    @scramble.command(name="jugar")
    async def jugar(self, ctx):
        if ctx.channel.id in scrambles_activos:
            datos = scrambles_activos[ctx.channel.id]
            embed = discord.Embed(
                description=f"❌ Ya hay un scramble activo: **{datos['mezclada'].upper()}**",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return

        if not PALABRAS_CACHE:
            await ctx.send(embed=discord.Embed(description="⏳ Cargando palabras... intentá en unos segundos.", color=COLOR_ERROR))
            asyncio.create_task(cargar_palabras_scramble())
            return

        palabra = random.choice(PALABRAS_CACHE)
        mezclada = mezclar_palabra(palabra)

        scrambles_activos[ctx.channel.id] = {
            "palabra": palabra,
            "mezclada": mezclada,
            "activa": True
        }

        # Mostrar letras con separación visual
        letras_display = "  ".join([f"**{l.upper()}**" for l in mezclada])

        embed = discord.Embed(
            title="🔀 ¡Scramble!",
            description=f"## {letras_display}",
            color=COLOR
        )
        embed.add_field(name="🔢 Letras", value=str(len(palabra)), inline=True)
        embed.add_field(name="⏱️ Tiempo", value="60 segundos", inline=True)
        embed.set_footer(text="Escribí la palabra en el chat para ganar | El primero en acertar gana")
        msg = await ctx.send(embed=embed)

        # Esperar 60 segundos, si nadie adivina revelar
        await asyncio.sleep(60)

        if ctx.channel.id in scrambles_activos and scrambles_activos[ctx.channel.id]["activa"]:
            del scrambles_activos[ctx.channel.id]
            embed_time = discord.Embed(
                title="⏱️ ¡Tiempo!",
                description=f"Nadie adivinó. La palabra era: **{palabra.upper()}**",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed_time)

    @scramble.command(name="terminar")
    @commands.has_permissions(administrator=True)
    async def terminar(self, ctx):
        if ctx.channel.id not in scrambles_activos:
            await ctx.send(embed=discord.Embed(description="❌ No hay scramble activo.", color=COLOR_ERROR))
            return
        datos = scrambles_activos.pop(ctx.channel.id)
        embed = discord.Embed(
            description=f"✅ Scramble terminado. La palabra era: **{datos['palabra'].upper()}**",
            color=COLOR
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Scramble(bot))