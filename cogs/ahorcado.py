import discord
from discord.ext import commands
import random
import asyncio
import aiohttp

COLOR       = discord.Color.orange()
COLOR_ERROR = discord.Color.red()
COLOR_WIN   = discord.Color.green()
COLOR_LOSE  = discord.Color.dark_red()

PALABRAS_URL = "https://raw.githubusercontent.com/ManiacDC/TypingAid/master/Wordlists/Wordlist%20Spanish.txt"
PALABRAS_CACHE: list[str] = []
PALABRAS_FALLBACK = [
    "chocolate","aventura","dinosaurio","telescopio","biblioteca",
    "helicoptero","electricidad","fotografia","universo","arquitectura",
    "revolucion","imaginacion","calendario","diccionario","hamburguesa",
    "submarino","laboratorio","laberinto","cocodrilo","mariposa",
    "montaña","cascada","volcan","guitarra","filosofia",
]

async def cargar_palabras():
    global PALABRAS_CACHE
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(PALABRAS_URL, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    lineas = (await r.text(errors="ignore")).splitlines()
                    PALABRAS_CACHE = [
                        p.strip().lower() for p in lineas
                        if p.strip().isalpha()
                        and 4 <= len(p.strip()) <= 12
                        and "k" not in p.lower()
                        and "w" not in p.lower()
                    ]
                    print(f"✅ Ahorcado: {len(PALABRAS_CACHE)} palabras cargadas")
                else:
                    PALABRAS_CACHE = PALABRAS_FALLBACK
    except Exception as e:
        print(f"⚠️ Ahorcado: {e}")
        PALABRAS_CACHE = PALABRAS_FALLBACK

def palabra_aleatoria():
    return random.choice(PALABRAS_CACHE or PALABRAS_FALLBACK)

# ─── TECLADO EN 2 PÁGINAS (25 letras sin K ni W) ──────────
# Página 0: A-M  |  Página 1: N-Z + Ñ
PAGINAS = [
    [["A","B","C","D","E"],
     ["F","G","H","I","J"],
     ["L","M","O","P","Q"]],
    [["N","Ñ","R","S","T"],
     ["U","V","X","Y","Z"],
     ["A","B","C","D","E"]],   # fila dummy — se usa para el botón de cambio
]
# Letras reales por página (sin la fila 2 de página 1 que es dummy)
LETRAS_P0 = [l for fila in PAGINAS[0] for l in fila]
LETRAS_P1 = [l for fila in PAGINAS[1][:2] for l in fila]

AHORCADO = [
    "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```",
]
MAX_ERRORES = 6
MAX_SALAS   = 3

# ─── PARTIDA ──────────────────────────────────────────────
class PartidaAhorcado:
    __slots__ = ("canal","modo","creador","modo_jugadores","adivinador",
                 "palabra","letras_usadas","errores","sala_id","mensaje_juego")

    def __init__(self, canal, modo, creador, modo_jugadores):
        self.canal          = canal
        self.modo           = modo
        self.creador        = creador
        self.modo_jugadores = modo_jugadores
        self.adivinador     = None
        self.palabra        = ""
        self.letras_usadas: set[str] = set()
        self.errores        = 0
        self.sala_id        = None
        self.mensaje_juego  = None

    def puede_jugar(self, user):
        if self.modo_jugadores == "solo":
            return user.id == self.adivinador.id
        return user.id != self.creador.id if self.modo == "pvp" else True

    def progreso(self):
        return " ".join(l.upper() if l.lower() in self.letras_usadas else "■" for l in self.palabra)

    def letras_falladas(self):
        return " ".join(sorted(l.upper() for l in self.letras_usadas if l not in self.palabra.lower()))

    def gano(self):
        return all(l.lower() in self.letras_usadas for l in self.palabra if l.isalpha())

    def perdio(self):
        return self.errores >= MAX_ERRORES

    def adivinar_letra(self, letra: str):
        letra = letra.lower()
        if letra in self.letras_usadas:
            return "ya_usada"
        self.letras_usadas.add(letra)
        if letra not in self.palabra.lower():
            self.errores += 1
            return "error"
        return "correcto"

# ─── REGISTRO DE PARTIDAS ─────────────────────────────────
_salas: dict[int, list[PartidaAhorcado]] = {}

def get_salas(cid):        return _salas.get(cid, [])
def agregar_sala(cid, p):  _salas.setdefault(cid, []).append(p)
def quitar_sala(cid, p):
    if cid in _salas:
        try: _salas[cid].remove(p)
        except ValueError: pass
        if not _salas[cid]: del _salas[cid]

# ─── EMBED ────────────────────────────────────────────────
def crear_embed(partida, titulo=None, color=None):
    e = discord.Embed(title=titulo or f"🎮 Ahorcado #{partida.sala_id}", color=color or COLOR)
    e.add_field(name="\u200b", value=AHORCADO[partida.errores], inline=False)
    e.add_field(name="\u200b", value=f"```\n{partida.progreso()}\n```", inline=False)
    falladas = partida.letras_falladas()
    e.add_field(name="❌ Falladas",  value=falladas or "—",              inline=True)
    e.add_field(name="💔 Errores",  value=f"{partida.errores}/{MAX_ERRORES}", inline=True)
    e.add_field(name="🔢 Letras",   value=str(len(partida.palabra)),    inline=True)
    if partida.modo == "pvp":
        e.add_field(name="✏️ Puso la palabra", value=partida.creador.display_name, inline=True)
    else:
        e.add_field(name="🤖 Modo", value="vs Bot", inline=True)
    e.add_field(name="👥 Puede adivinar",
                value="Solo el adivinador" if partida.modo_jugadores=="solo" else "Todos del canal",
                inline=True)
    if partida.adivinador:
        e.add_field(name="🎯 Adivinador", value=partida.adivinador.display_name, inline=True)
    e.set_footer(text="🟢 Verde = acierto  🔴 Rojo = fallo  ➡️ Botón azul = cambiar página")
    return e

# ─── TECLADO CON PAGINACIÓN ───────────────────────────────
def _estilo(letra, partida):
    l = letra.lower()
    if l not in partida.letras_usadas:
        return discord.ButtonStyle.secondary
    return discord.ButtonStyle.success if l in partida.palabra.lower() else discord.ButtonStyle.danger

class VistaTeclado(discord.ui.View):
    def __init__(self, partida, pagina=0):
        super().__init__(timeout=600)
        self.partida = partida
        self.pagina  = pagina
        self._build()

    def _build(self):
        filas = PAGINAS[self.pagina]
        letras_pagina = LETRAS_P0 if self.pagina == 0 else LETRAS_P1

        for fila_idx, fila in enumerate(filas[:2]):   # solo 2 filas de letras
            for letra in fila:
                btn = discord.ui.Button(
                    label=letra,
                    style=_estilo(letra, self.partida),
                    custom_id=f"ah{self.partida.sala_id}_{self.pagina}_{letra}",
                    row=fila_idx
                )
                btn.callback = self._cb(letra)
                self.add_item(btn)

        # Fila 2: letras restantes (hasta 4) + botón cambiar página
        letras_fila2 = filas[2] if len(filas) > 2 else []
        # En página 0 la fila 2 tiene letras reales
        if self.pagina == 0:
            for letra in letras_fila2:
                btn = discord.ui.Button(
                    label=letra,
                    style=_estilo(letra, self.partida),
                    custom_id=f"ah{self.partida.sala_id}_{self.pagina}_{letra}",
                    row=2
                )
                btn.callback = self._cb(letra)
                self.add_item(btn)

        # Botón cambiar página (siempre en fila 3)
        otra = 1 if self.pagina == 0 else 0
        label_btn = "N→Z ➡️" if self.pagina == 0 else "⬅️ A→M"
        btn_cambiar = discord.ui.Button(
            label=label_btn,
            style=discord.ButtonStyle.primary,
            custom_id=f"ah{self.partida.sala_id}_page",
            row=3
        )
        btn_cambiar.callback = self._cambiar_pagina(otra)
        self.add_item(btn_cambiar)

    def _cb(self, letra):
        async def callback(interaction: discord.Interaction):
            if not self.partida.puede_jugar(interaction.user):
                await interaction.response.send_message("No podés jugar en esta partida.", ephemeral=True)
                return
            if letra.lower() in self.partida.letras_usadas:
                await interaction.response.send_message(f"Ya usaste la **{letra.upper()}**.", ephemeral=True)
                return

            resultado = self.partida.adivinar_letra(letra)
            self.stop()

            if self.partida.gano():
                emb = crear_embed(self.partida, f"🎉 ¡Ganaste! — Ahorcado #{self.partida.sala_id}", COLOR_WIN)
                emb.add_field(name="🏆 La palabra era", value=f"**{self.partida.palabra.upper()}**", inline=False)
                await interaction.response.edit_message(embed=emb, view=None)
                quitar_sala(self.partida.canal.id, self.partida)
            elif self.partida.perdio():
                emb = crear_embed(self.partida, f"💀 ¡Perdiste! — Ahorcado #{self.partida.sala_id}", COLOR_LOSE)
                emb.add_field(name="La palabra era", value=f"**{self.partida.palabra.upper()}**", inline=False)
                await interaction.response.edit_message(embed=emb, view=None)
                quitar_sala(self.partida.canal.id, self.partida)
            else:
                msg = f"✅ ¡La **{letra.upper()}** está!" if resultado=="correcto" else f"❌ La **{letra.upper()}** no está."
                await interaction.response.send_message(msg, ephemeral=True)
                await interaction.message.edit(embed=crear_embed(self.partida), view=VistaTeclado(self.partida, self.pagina))
        return callback

    def _cambiar_pagina(self, nueva_pag):
        async def callback(interaction: discord.Interaction):
            if not self.partida.puede_jugar(interaction.user):
                await interaction.response.send_message("No podés jugar en esta partida.", ephemeral=True)
                return
            self.stop()
            await interaction.response.edit_message(
                embed=crear_embed(self.partida),
                view=VistaTeclado(self.partida, nueva_pag)
            )
        return callback

    async def on_timeout(self):
        quitar_sala(self.partida.canal.id, self.partida)

# ─── MODAL PALABRA SECRETA ────────────────────────────────
class ModalPalabra(discord.ui.Modal, title="Ingresá tu palabra secreta"):
    inp = discord.ui.TextInput(
        label="Palabra secreta (sin K ni W)",
        style=discord.TextStyle.short,
        placeholder="Ej: elefante",
        min_length=2, max_length=12, required=True
    )

    def __init__(self, partida): super().__init__(); self.partida = partida

    async def on_submit(self, interaction: discord.Interaction):
        palabra = self.inp.value.strip().lower()
        if not palabra.isalpha() or len(palabra) < 2:
            await interaction.response.send_message("❌ Solo letras, mínimo 2.", ephemeral=True); return
        if "k" in palabra or "w" in palabra:
            await interaction.response.send_message("❌ No se permiten K ni W.", ephemeral=True); return

        self.partida.palabra = palabra
        emb = discord.Embed(
            title=f"🎮 Ahorcado #{self.partida.sala_id} — PvP",
            description=f"**{self.partida.creador.display_name}** ya tiene su palabra secreta.\n¿Quién se anima?",
            color=COLOR
        )
        emb.add_field(name="🔢 Longitud", value=f"`{'_ ' * len(palabra)}`", inline=False)
        emb.add_field(name="👥 Puede adivinar",
                      value="Solo el adivinador designado" if self.partida.modo_jugadores=="solo" else "Todos del canal",
                      inline=True)
        emb.set_footer(text="Presioná ✅ Unirse para ser el adivinador")
        await interaction.message.edit(embed=emb, view=VistaSala(self.partida))
        await interaction.response.send_message("✅ Palabra guardada. Nadie la vio.", ephemeral=True)

# ─── VISTAS DE SALA ───────────────────────────────────────
class VistaConfig(discord.ui.View):
    def __init__(self, ctx, modo):
        super().__init__(timeout=60)
        self.ctx = ctx; self.modo = modo

    async def on_timeout(self): pass   # no hay sala creada todavía, nada que limpiar

    async def _elegir(self, interaction, modo_jug):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Solo el creador puede elegir.", ephemeral=True); return
        self.stop()
        await interaction.response.edit_message(content="⚙️ Creando sala...", embed=None, view=None)
        await _crear_partida(self.ctx, self.modo, modo_jug, interaction.message)

    @discord.ui.button(label="🙋 Solo yo adivino",       style=discord.ButtonStyle.primary)
    async def solo(self, i, b): await self._elegir(i, "solo")

    @discord.ui.button(label="👥 Todos pueden adivinar", style=discord.ButtonStyle.success)
    async def todos(self, i, b): await self._elegir(i, "todos")

    @discord.ui.button(label="❌ Cancelar",               style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction, button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Solo el creador puede cancelar.", ephemeral=True); return
        self.stop()
        await interaction.message.delete()

class VistaIngresarPalabra(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=120); self.partida = partida

    async def on_timeout(self): quitar_sala(self.partida.canal.id, self.partida)

    @discord.ui.button(label="✏️ Ingresar mi palabra (solo vos la ves)", style=discord.ButtonStyle.primary)
    async def ingresar(self, interaction, button):
        if interaction.user.id != self.partida.creador.id:
            await interaction.response.send_message("Solo el creador puede ingresar la palabra.", ephemeral=True); return
        self.stop()
        await interaction.response.send_modal(ModalPalabra(self.partida))

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction, button):
        if interaction.user.id != self.partida.creador.id:
            await interaction.response.send_message("Solo el creador puede cancelar.", ephemeral=True); return
        self.stop()
        quitar_sala(self.partida.canal.id, self.partida)
        await interaction.message.edit(content="❌ Sala cancelada.", embed=None, view=None)
        await interaction.response.send_message("Cancelado.", ephemeral=True)

class VistaSala(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=300); self.partida = partida

    async def on_timeout(self): quitar_sala(self.partida.canal.id, self.partida)

    @discord.ui.button(label="✅ Unirse como adivinador", style=discord.ButtonStyle.success)
    async def unirse(self, interaction, button):
        if interaction.user.id == self.partida.creador.id:
            await interaction.response.send_message("Vos pusiste la palabra, no podés adivinar.", ephemeral=True); return
        if self.partida.adivinador:
            await interaction.response.send_message("Ya hay un adivinador principal.", ephemeral=True); return
        self.partida.adivinador = interaction.user
        self.stop()
        await interaction.response.send_message("✅ ¡Sos el adivinador!", ephemeral=True)
        await interaction.message.edit(
            embed=crear_embed(self.partida, f"🎮 Ahorcado #{self.partida.sala_id} — ¡Comienza!"),
            view=VistaTeclado(self.partida)
        )

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction, button):
        if interaction.user.id != self.partida.creador.id:
            await interaction.response.send_message("Solo el creador puede cancelar.", ephemeral=True); return
        self.stop()
        quitar_sala(self.partida.canal.id, self.partida)
        await interaction.message.edit(content="❌ Sala cancelada.", embed=None, view=None)
        await interaction.response.send_message("Cancelado.", ephemeral=True)

# ─── CREAR PARTIDA ────────────────────────────────────────
async def _crear_partida(ctx, modo, modo_jugadores, msg_config):
    cid     = ctx.channel.id
    num     = len(get_salas(cid)) + 1
    partida = PartidaAhorcado(ctx.channel, modo, ctx.author, modo_jugadores)
    partida.sala_id = num
    agregar_sala(cid, partida)

    try: await msg_config.delete()
    except: pass

    if modo == "pvbot":
        partida.adivinador = ctx.author
        partida.palabra    = palabra_aleatoria()
        emb = crear_embed(partida, f"🤖 Ahorcado #{num} — vs Bot")
        partida.mensaje_juego = await ctx.channel.send(embed=emb, view=VistaTeclado(partida))
    else:
        emb = discord.Embed(
            title=f"🎮 Ahorcado #{num} — PvP",
            description=f"**{ctx.author.display_name}** va a ingresar su palabra secreta.",
            color=COLOR
        )
        partida.mensaje_juego = await ctx.channel.send(embed=emb, view=VistaIngresarPalabra(partida))

# ─── COG ──────────────────────────────────────────────────
class Ahorcado(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not PALABRAS_CACHE: await cargar_palabras()

    @commands.group(name="ahorcado", aliases=["ah"], invoke_without_command=True)
    async def ahorcado(self, ctx):
        info = f"{len(PALABRAS_CACHE):,}" if PALABRAS_CACHE else "fallback"
        e = discord.Embed(title="🎮 Ahorcado — Ayuda", color=COLOR)
        e.add_field(name="$ah pvp",      value="Vos ponés la palabra, otro(s) la adivinan.",        inline=False)
        e.add_field(name="$ah bot",      value="El bot elige una palabra al azar.",                  inline=False)
        e.add_field(name="$ah terminar", value="Termina todas las partidas del canal (solo admins).", inline=False)
        e.add_field(name="📌 Límite",    value=f"Hasta {MAX_SALAS} partidas por canal",             inline=True)
        e.add_field(name="📚 Diccionario",value=f"{info} palabras",                                  inline=True)
        await ctx.send(embed=e)

    @ahorcado.command(name="pvp")
    async def pvp(self, ctx):
        if len(get_salas(ctx.channel.id)) >= MAX_SALAS:
            await ctx.send(embed=discord.Embed(description=f"❌ Ya hay {MAX_SALAS} partidas en este canal.", color=COLOR_ERROR)); return
        await ctx.send(
            embed=discord.Embed(title="🎮 Ahorcado — PvP", description="**¿Quién puede adivinar?**", color=COLOR),
            view=VistaConfig(ctx, "pvp")
        )

    @ahorcado.command(name="bot")
    async def vs_bot(self, ctx):
        if len(get_salas(ctx.channel.id)) >= MAX_SALAS:
            await ctx.send(embed=discord.Embed(description=f"❌ Ya hay {MAX_SALAS} partidas en este canal.", color=COLOR_ERROR)); return
        if not PALABRAS_CACHE:
            await ctx.send(embed=discord.Embed(description="⏳ Cargando diccionario...", color=COLOR_ERROR))
            asyncio.create_task(cargar_palabras()); return
        await ctx.send(
            embed=discord.Embed(title="🤖 Ahorcado — vs Bot", description="**¿Quién puede adivinar?**", color=COLOR),
            view=VistaConfig(ctx, "pvbot")
        )

    @ahorcado.command(name="terminar")
    @commands.has_permissions(administrator=True)
    async def terminar(self, ctx):
        salas = get_salas(ctx.channel.id)
        if not salas:
            await ctx.send(embed=discord.Embed(description="❌ No hay partidas activas.", color=COLOR_ERROR)); return
        n = len(salas)
        _salas.pop(ctx.channel.id, None)
        await ctx.send(embed=discord.Embed(description=f"✅ {n} partida(s) terminada(s).", color=COLOR))

async def setup(bot):
    await bot.add_cog(Ahorcado(bot))