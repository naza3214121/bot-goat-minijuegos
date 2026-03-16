import discord
from discord.ext import commands
import random
import asyncio
import aiohttp

COLOR = discord.Color.green()
COLOR_ERROR = discord.Color.red()
COLOR_WIN = discord.Color.gold()

PALABRAS_URL = "https://raw.githubusercontent.com/ManiacDC/TypingAid/master/Wordlists/Wordlist%20Spanish.txt"
PALABRAS_5 = []

async def cargar_palabras_wordle():
    global PALABRAS_5
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PALABRAS_URL, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    texto = await resp.text(encoding="utf-8", errors="ignore")
                    todas = texto.strip().splitlines()
                    PALABRAS_5 = [
                        p.strip().lower() for p in todas
                        if p.strip().isalpha() and len(p.strip()) == 5
                    ]
                    print(f"✅ Wordle: {len(PALABRAS_5)} palabras de 5 letras cargadas")
                else:
                    PALABRAS_5 = FALLBACK_5
    except:
        PALABRAS_5 = FALLBACK_5

FALLBACK_5 = [
    "gatos", "perro", "cielo", "verde", "playa", "torre", "monte", "tierra",
    "fuego", "agua", "viento", "noche", "plaza", "libro", "campo", "bosque",
    "carta", "marco", "lunar", "feria", "radio", "salud", "motor", "color",
    "baile", "breve", "claro", "dulce", "enero", "flota", "gotas", "horno",
    "lento", "magia", "novio", "padre", "queso", "reina", "sabio", "techo",
]

MAX_INTENTOS = 6
partidas_wordle: dict = {}

VERDE = "🟩"
AMARILLO = "🟨"
GRIS = "⬛"

def evaluar_intento(palabra_secreta, intento):
    resultado = []
    secreta_lista = list(palabra_secreta)
    intento_lista = list(intento)
    marcado = [False] * 5

    # Primera pasada: verdes
    colores = [""] * 5
    for i in range(5):
        if intento_lista[i] == secreta_lista[i]:
            colores[i] = "verde"
            marcado[i] = True

    # Segunda pasada: amarillos y grises
    for i in range(5):
        if colores[i] == "verde":
            continue
        encontrado = False
        for j in range(5):
            if not marcado[j] and intento_lista[i] == secreta_lista[j]:
                colores[i] = "amarillo"
                marcado[j] = True
                encontrado = True
                break
        if not encontrado:
            colores[i] = "gris"

    return colores

def render_intento(intento, colores):
    emojis = {"verde": VERDE, "amarillo": AMARILLO, "gris": GRIS}
    linea_colores = "".join([emojis[c] for c in colores])
    linea_letras = " ".join([f"`{l.upper()}`" for l in intento])
    return f"{linea_colores}\n{linea_letras}"

class PartidaWordle:
    def __init__(self, canal, jugador, palabra):
        self.canal = canal
        self.jugador = jugador
        self.palabra = palabra
        self.intentos = []
        self.colores_intentos = []
        self.intentos_restantes = MAX_INTENTOS
        self.letras_verdes = set()
        self.letras_amarillas = set()
        self.letras_grises = set()

class VistaIngresarLetra(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=120)
        self.partida = partida

    @discord.ui.button(label="📝 Ingresar intento", style=discord.ButtonStyle.primary)
    async def ingresar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.partida.jugador.id:
            await interaction.response.send_message("No es tu partida.", ephemeral=True)
            return

        await interaction.response.send_message(
            embed=discord.Embed(
                title="📝 Escribí una palabra de 5 letras",
                description="Tenés 60 segundos.",
                color=COLOR
            ),
            ephemeral=True
        )

        def check(m):
            return m.author.id == self.partida.jugador.id and m.channel.id == self.partida.canal.id

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=60)
            intento = msg.content.strip().lower()
            try:
                await msg.delete()
            except:
                pass

            if not intento.isalpha() or len(intento) != 5:
                await self.partida.canal.send(
                    embed=discord.Embed(description="❌ La palabra debe tener exactamente 5 letras.", color=COLOR_ERROR),
                    delete_after=4
                )
                return

            self.stop()
            await procesar_intento(self.partida, intento, interaction.message)

        except asyncio.TimeoutError:
            pass

    async def on_timeout(self):
        partidas_wordle.pop(self.partida.canal.id, None)

def crear_embed_wordle(partida, titulo=None, color=None):
    embed = discord.Embed(
        title=titulo or f"🟩 Wordle — {MAX_INTENTOS - partida.intentos_restantes}/{MAX_INTENTOS}",
        color=color or COLOR
    )

    # Historial de intentos
    if partida.intentos:
        historial = "\n\n".join([
            render_intento(intento, colores)
            for intento, colores in zip(partida.intentos, partida.colores_intentos)
        ])
        embed.add_field(name="📋 Intentos", value=historial, inline=False)

    # Intentos vacíos restantes
    vacios = partida.intentos_restantes
    if vacios > 0 and len(partida.intentos) < MAX_INTENTOS:
        embed.add_field(name=f"⬜ Restantes: {vacios}", value="\n".join(["⬜⬜⬜⬜⬜"] * vacios), inline=False)

    # Pistas de letras
    if partida.letras_verdes:
        embed.add_field(name="🟩 En posición correcta", value=" ".join([f"`{l.upper()}`" for l in sorted(partida.letras_verdes)]), inline=True)
    if partida.letras_amarillas:
        embed.add_field(name="🟨 En la palabra", value=" ".join([f"`{l.upper()}`" for l in sorted(partida.letras_amarillas)]), inline=True)
    if partida.letras_grises:
        embed.add_field(name="⬛ No están", value=" ".join([f"`{l.upper()}`" for l in sorted(partida.letras_grises)]), inline=True)

    embed.set_footer(text="🟩 Letra correcta | 🟨 En la palabra, lugar incorrecto | ⬛ No está")
    return embed

async def procesar_intento(partida, intento, mensaje):
    colores = evaluar_intento(partida.palabra, intento)
    partida.intentos.append(intento)
    partida.colores_intentos.append(colores)
    partida.intentos_restantes -= 1

    for i, (letra, color) in enumerate(zip(intento, colores)):
        if color == "verde":
            partida.letras_verdes.add(letra)
            partida.letras_amarillas.discard(letra)
        elif color == "amarillo":
            if letra not in partida.letras_verdes:
                partida.letras_amarillas.add(letra)
        else:
            if letra not in partida.letras_verdes and letra not in partida.letras_amarillas:
                partida.letras_grises.add(letra)

    if all(c == "verde" for c in colores):
        embed = crear_embed_wordle(partida, "🎉 ¡Adivinaste!", COLOR_WIN)
        embed.add_field(name="🏆 La palabra era", value=f"**{partida.palabra.upper()}**", inline=False)
        await mensaje.edit(embed=embed, view=None)
        partidas_wordle.pop(partida.canal.id, None)
        return

    if partida.intentos_restantes == 0:
        embed = crear_embed_wordle(partida, "💀 ¡Sin intentos!", COLOR_ERROR)
        embed.add_field(name="La palabra era", value=f"**{partida.palabra.upper()}**", inline=False)
        await mensaje.edit(embed=embed, view=None)
        partidas_wordle.pop(partida.canal.id, None)
        return

    embed = crear_embed_wordle(partida)
    await mensaje.edit(embed=embed, view=VistaIngresarLetra(partida))

class Wordle(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not PALABRAS_5:
            await cargar_palabras_wordle()

    @commands.group(name="wordle", invoke_without_command=True)
    async def wordle(self, ctx):
        embed = discord.Embed(title="🟩 Wordle — Ayuda", color=COLOR)
        embed.add_field(name="$wordle crear", value="Empieza una partida de Wordle.", inline=False)
        embed.add_field(name="Reglas", value="Tenés 6 intentos para adivinar una palabra de 5 letras.\n🟩 = letra correcta en posición correcta\n🟨 = letra en la palabra pero lugar incorrecto\n⬛ = letra no está en la palabra", inline=False)
        await ctx.send(embed=embed)

    @wordle.command(name="crear")
    async def crear(self, ctx):
        if ctx.channel.id in partidas_wordle:
            await ctx.send(embed=discord.Embed(description="❌ Ya hay una partida en este canal.", color=COLOR_ERROR))
            return
        if not PALABRAS_5:
            await ctx.send(embed=discord.Embed(description="⏳ Cargando palabras... intentá en unos segundos.", color=COLOR_ERROR))
            asyncio.create_task(cargar_palabras_wordle())
            return

        palabra = random.choice(PALABRAS_5)
        partida = PartidaWordle(ctx.channel, ctx.author, palabra)
        partidas_wordle[ctx.channel.id] = partida

        embed = crear_embed_wordle(partida, "🟩 ¡Wordle!")
        await ctx.send(embed=embed, view=VistaIngresarLetra(partida))

    @wordle.command(name="terminar")
    @commands.has_permissions(administrator=True)
    async def terminar(self, ctx):
        if ctx.channel.id not in partidas_wordle:
            await ctx.send(embed=discord.Embed(description="❌ No hay partida activa.", color=COLOR_ERROR))
            return
        del partidas_wordle[ctx.channel.id]
        await ctx.send(embed=discord.Embed(description="✅ Partida terminada.", color=COLOR))

async def setup(bot):
    await bot.add_cog(Wordle(bot))
