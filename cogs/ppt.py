import discord
from discord.ext import commands
import random
import asyncio

COLOR = discord.Color.blue()
COLOR_ERROR = discord.Color.red()
COLOR_WIN = discord.Color.green()

OPCIONES = {"🪨 Piedra": "piedra", "📄 Papel": "papel", "✂️ Tijeras": "tijeras"}
GANA = {"piedra": "tijeras", "papel": "piedra", "tijeras": "papel"}
EMOJI = {"piedra": "🪨", "papel": "📄", "tijeras": "✂️"}

partidas_ppt: dict = {}

class PartidaPPT:
    def __init__(self, canal, jugador1, best_of):
        self.canal = canal
        self.jugador1 = jugador1
        self.jugador2 = None
        self.best_of = best_of
        self.victorias = {jugador1.id: 0}
        self.elecciones = {}
        self.ronda = 0

    def rondas_para_ganar(self): return (self.best_of // 2) + 1

class VistaSalaPPT(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=120)
        self.partida = partida

    async def on_timeout(self):
        partidas_ppt.pop(self.partida.canal.id, None)

    @discord.ui.button(label="⚔️ Aceptar desafío", style=discord.ButtonStyle.success)
    async def aceptar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.partida.jugador1.id:
            await interaction.response.send_message("No podés desafiarte a vos mismo.", ephemeral=True)
            return
        if self.partida.jugador2:
            await interaction.response.send_message("Ya hay un rival.", ephemeral=True)
            return
        self.partida.jugador2 = interaction.user
        self.partida.victorias[interaction.user.id] = 0
        self.stop()
        await interaction.response.edit_message(view=None)
        await iniciar_ronda_ppt(self.partida, interaction.message)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.partida.jugador1.id:
            await interaction.response.send_message("Solo el creador puede cancelar.", ephemeral=True)
            return
        self.stop()
        partidas_ppt.pop(self.partida.canal.id, None)
        await interaction.message.edit(content="❌ Desafío cancelado.", embed=None, view=None)
        await interaction.response.send_message("Cancelado.", ephemeral=True)

class VistaElegirPPT(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=30)
        self.partida = partida
        self._terminado = False

        for label, valor in OPCIONES.items():
            btn = discord.ui.Button(label=label, style=discord.ButtonStyle.primary)
            btn.callback = self._elegir(valor)
            self.add_item(btn)

    def _elegir(self, valor):
        async def callback(interaction: discord.Interaction):
            uid = interaction.user.id
            if uid not in [self.partida.jugador1.id, self.partida.jugador2.id]:
                await interaction.response.send_message("No estás en esta partida.", ephemeral=True)
                return
            if uid in self.partida.elecciones:
                await interaction.response.send_message("Ya elegiste.", ephemeral=True)
                return

            self.partida.elecciones[uid] = valor
            await interaction.response.send_message(f"✅ Elegiste **{EMOJI[valor]} {valor.capitalize()}**. Esperando al rival...", ephemeral=True)

            if len(self.partida.elecciones) == 2 and not self._terminado:
                self._terminado = True
                self.stop()
        return callback

    async def on_timeout(self):
        if not self._terminado:
            self._terminado = True
            self.stop()

async def iniciar_ronda_ppt(partida, mensaje):
    need = partida.rondas_para_ganar()

    while True:
        if partida.canal.id not in partidas_ppt:
            return

        partida.ronda += 1
        partida.elecciones = {}

        v1 = partida.victorias[partida.jugador1.id]
        v2 = partida.victorias[partida.jugador2.id]

        embed = discord.Embed(
            title=f"🪨📄✂️ Piedra Papel o Tijeras — Ronda {partida.ronda}",
            description=f"**{partida.jugador1.display_name}** vs **{partida.jugador2.display_name}**",
            color=COLOR
        )
        embed.add_field(name="🏆 Marcador", value=f"{partida.jugador1.display_name}: **{v1}** | {partida.jugador2.display_name}: **{v2}**", inline=False)
        embed.add_field(name="🎯 Primero en ganar", value=f"**{need}** rondas gana la partida", inline=True)
        embed.set_footer(text="Elegí en secreto — tenés 30 segundos")

        vista = VistaElegirPPT(partida)
        await mensaje.edit(embed=embed, view=vista)
        await vista.wait()

        j1, j2 = partida.jugador1, partida.jugador2
        e1 = partida.elecciones.get(j1.id)
        e2 = partida.elecciones.get(j2.id)

        # Casos de timeout/no eligió
        if not e1 and not e2:
            desc = "⏱️ Ninguno eligió. Ronda anulada."
            ganador_ronda = None
        elif not e1:
            partida.victorias[j2.id] += 1
            desc = f"⏱️ **{j1.display_name}** no eligió. Punto para **{j2.display_name}**."
            ganador_ronda = j2
        elif not e2:
            partida.victorias[j1.id] += 1
            desc = f"⏱️ **{j2.display_name}** no eligió. Punto para **{j1.display_name}**."
            ganador_ronda = j1
        elif e1 == e2:
            desc = f"🤝 **Empate** — {EMOJI[e1]} vs {EMOJI[e2]}"
            ganador_ronda = None
        elif GANA[e1] == e2:
            partida.victorias[j1.id] += 1
            desc = f"🏅 **{j1.display_name}** gana — {EMOJI[e1]} vence a {EMOJI[e2]}"
            ganador_ronda = j1
        else:
            partida.victorias[j2.id] += 1
            desc = f"🏅 **{j2.display_name}** gana — {EMOJI[e2]} vence a {EMOJI[e1]}"
            ganador_ronda = j2

        embed_res = discord.Embed(
            title=f"Ronda {partida.ronda} — Resultado",
            description=desc,
            color=COLOR_WIN if ganador_ronda else COLOR
        )
        embed_res.add_field(
            name="Marcador",
            value=f"{j1.display_name}: **{partida.victorias[j1.id]}** | {j2.display_name}: **{partida.victorias[j2.id]}**"
        )
        await mensaje.edit(embed=embed_res, view=None)

        # Verificar ganador de la partida
        for jug in [j1, j2]:
            if partida.victorias[jug.id] >= need:
                rival = j2 if jug.id == j1.id else j1
                embed_final = discord.Embed(
                    title=f"🏆 ¡{jug.display_name} gana la partida!",
                    description=f"**{jug.display_name}** {partida.victorias[jug.id]} — {partida.victorias[rival.id]} **{rival.display_name}**",
                    color=COLOR_WIN
                )
                await partida.canal.send(embed=embed_final)
                partidas_ppt.pop(partida.canal.id, None)
                return

        await asyncio.sleep(3)

class PiedraPapelTijeras(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.group(name="ppt", invoke_without_command=True)
    async def ppt(self, ctx):
        embed = discord.Embed(title="🪨📄✂️ Piedra Papel o Tijeras — Ayuda", color=COLOR)
        embed.add_field(name="$ppt crear [al mejor de X]", value="Crea un desafío.\nEjemplo: `$ppt crear 3` (al mejor de 3)", inline=False)
        embed.add_field(name="$ppt terminar", value="Termina la partida (solo admins).", inline=False)
        await ctx.send(embed=embed)

    @ppt.command(name="crear")
    async def crear(self, ctx, best_of: int = 3):
        if ctx.channel.id in partidas_ppt:
            await ctx.send(embed=discord.Embed(description="❌ Ya hay una partida en este canal.", color=COLOR_ERROR))
            return
        if best_of not in [1, 3, 5, 7]:
            await ctx.send(embed=discord.Embed(description="❌ Usá 1, 3, 5 o 7 como best of.", color=COLOR_ERROR))
            return

        partida = PartidaPPT(ctx.channel, ctx.author, best_of)
        partidas_ppt[ctx.channel.id] = partida

        embed = discord.Embed(
            title="🪨📄✂️ ¡Desafío de Piedra Papel o Tijeras!",
            description=f"**{ctx.author.display_name}** desafía a quien se anime.",
            color=COLOR
        )
        embed.add_field(name="🎯 Modalidad", value=f"Al mejor de **{best_of}**", inline=True)
        embed.set_footer(text="Presioná ⚔️ Aceptar desafío para jugar")
        await ctx.send(embed=embed, view=VistaSalaPPT(partida))

    @ppt.command(name="terminar")
    @commands.has_permissions(administrator=True)
    async def terminar(self, ctx):
        if ctx.channel.id not in partidas_ppt:
            await ctx.send(embed=discord.Embed(description="❌ No hay partida activa.", color=COLOR_ERROR))
            return
        del partidas_ppt[ctx.channel.id]
        await ctx.send(embed=discord.Embed(description="✅ Partida terminada.", color=COLOR))

async def setup(bot):
    await bot.add_cog(PiedraPapelTijeras(bot))
