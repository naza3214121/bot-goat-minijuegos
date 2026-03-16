import discord
from discord.ext import commands
import asyncio

COLOR       = discord.Color.purple()
COLOR_ERROR = discord.Color.red()
COLOR_WIN   = discord.Color.green()

partidas_nn: dict = {}

class PartidaNuncaNunca:
    def __init__(self, canal, creador, max_jugadores):
        self.canal          = canal
        self.creador        = creador
        self.max_jugadores  = max_jugadores
        self.jugadores:     list = []
        self.jugadores_map: dict = {}
        self.ronda_actual   = 0

    def jugador_turno(self): return self.jugadores[self.ronda_actual]
    def total_rondas(self):  return len(self.jugadores)

# ─── VISTA SALA ───────────────────────────────────────────
class VistaSalaNunca(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=300)
        self.partida = partida

    async def on_timeout(self):
        partidas_nn.pop(self.partida.canal.id, None)

    @discord.ui.button(label="✅ Unirse", style=discord.ButtonStyle.success)
    async def unirse(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.partida.jugadores_map:
            await interaction.response.send_message("Ya estás en la partida.", ephemeral=True)
            return
        if len(self.partida.jugadores) >= self.partida.max_jugadores:
            await interaction.response.send_message("La sala está llena.", ephemeral=True)
            return

        datos = {"uid": uid, "nombre": interaction.user.display_name, "member": interaction.user, "veces": 0}
        self.partida.jugadores.append(datos)
        self.partida.jugadores_map[uid] = datos

        nombres = ", ".join([j["nombre"] for j in self.partida.jugadores])
        embed = interaction.message.embeds[0]
        embed.set_field_at(1, name=f"Jugadores ({len(self.partida.jugadores)}/{self.partida.max_jugadores})", value=nombres)
        await interaction.message.edit(embed=embed)
        await interaction.response.send_message("✅ ¡Te uniste!", ephemeral=True)

    @discord.ui.button(label="🚀 Iniciar", style=discord.ButtonStyle.primary)
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.partida.creador.id:
            await interaction.response.send_message("Solo el creador puede iniciar.", ephemeral=True)
            return
        if len(self.partida.jugadores) < 2:
            await interaction.response.send_message("Necesitás al menos 2 jugadores.", ephemeral=True)
            return
        self.stop()
        await interaction.message.edit(view=None)
        await interaction.response.send_message("🚀 ¡Arrancamos!", ephemeral=True)
        await siguiente_ronda(self.partida)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.partida.creador.id:
            await interaction.response.send_message("Solo el creador puede cancelar.", ephemeral=True)
            return
        self.stop()
        partidas_nn.pop(self.partida.canal.id, None)
        await interaction.message.edit(content="❌ Sala cancelada.", embed=None, view=None)
        await interaction.response.send_message("Cancelado.", ephemeral=True)

# ─── VISTA ESCRIBIR FRASE ─────────────────────────────────
class VistaEscribirFrase(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=120)
        self.partida    = partida
        self.frase_lista = False
        self._wait_task  = None   # FIX 2: referencia para cancelar el wait_for

    async def on_timeout(self):
        if self.frase_lista:
            return

        # FIX 2: cancelar el wait_for para que no capture el próximo mensaje
        if self._wait_task and not self._wait_task.done():
            self._wait_task.cancel()

        quitar = self.partida.jugador_turno()
        await self.partida.canal.send(
            embed=discord.Embed(
                description=f"⏱️ **{quitar['nombre']}** tardó demasiado. Se saltea su turno.",
                color=COLOR_ERROR
            )
        )
        self.partida.ronda_actual += 1
        if self.partida.ronda_actual >= self.partida.total_rondas():
            await mostrar_resultado_final(self.partida)
        else:
            await siguiente_ronda(self.partida)

    @discord.ui.button(label="✏️ Escribir mi frase", style=discord.ButtonStyle.primary)
    async def escribir(self, interaction: discord.Interaction, button: discord.ui.Button):
        turno = self.partida.jugador_turno()
        if interaction.user.id != turno["uid"]:
            await interaction.response.send_message("No es tu turno de poner la frase.", ephemeral=True)
            return

        # FIX 1: anti-doble click
        if self.frase_lista:
            await interaction.response.send_message("La frase ya fue ingresada.", ephemeral=True)
            return
        self.frase_lista = True

        # Deshabilitar el botón visualmente
        button.disabled = True
        await interaction.message.edit(view=self)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✏️ Escribí tu frase de Nunca Nunca",
                description="Ejemplo: *Nunca nunca me quedé dormido en clase*\nTenés 90 segundos.",
                color=COLOR
            ),
            ephemeral=True
        )

        def check(m):
            return m.author.id == turno["uid"] and m.channel.id == self.partida.canal.id

        # FIX 2: guardar como task para poder cancelarla desde on_timeout
        self._wait_task = asyncio.get_event_loop().create_task(
            interaction.client.wait_for("message", check=check, timeout=90)
        )

        try:
            msg = await self._wait_task
        except (asyncio.TimeoutError, asyncio.CancelledError):
            self.frase_lista = False
            return

        frase = msg.content.strip()
        try:
            await msg.delete()
        except:
            pass

        if len(frase) < 5:
            self.frase_lista = False
            button.disabled = False
            await interaction.message.edit(view=self)
            await self.partida.canal.send(
                embed=discord.Embed(description="❌ La frase es muy corta.", color=COLOR_ERROR),
                delete_after=4
            )
            return

        self.stop()
        await interaction.message.edit(view=None)
        await mostrar_votacion(self.partida, frase, interaction.message)

# ─── VISTA VOTACIÓN ───────────────────────────────────────
class VistaVotoNunca(discord.ui.View):
    def __init__(self, partida, frase):
        super().__init__(timeout=30)
        self.partida      = partida
        self.frase        = frase
        self.votos_si     = []
        self.votos_no     = []
        self._terminado   = False
        self.turno_uid    = self.partida.jugador_turno()["uid"]
        self.pueden_votar = [j["uid"] for j in self.partida.jugadores if j["uid"] != self.turno_uid]

    @discord.ui.button(label="✋ Yo lo hice", style=discord.ButtonStyle.danger)
    async def si(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid == self.turno_uid:
            await interaction.response.send_message("Vos pusiste la frase, no podés votar.", ephemeral=True)
            return
        if uid not in self.partida.jugadores_map:
            await interaction.response.send_message("No estás en esta partida.", ephemeral=True)
            return
        if uid in self.votos_si or uid in self.votos_no:
            await interaction.response.send_message("Ya votaste.", ephemeral=True)
            return
        self.votos_si.append(uid)
        self.partida.jugadores_map[uid]["veces"] += 1
        await interaction.response.send_message("✋ ¡Registrado!", ephemeral=True)
        if len(self.votos_si) + len(self.votos_no) >= len(self.pueden_votar) and not self._terminado:
            self._terminado = True
            self.stop()

    @discord.ui.button(label="🙅 Nunca lo hice", style=discord.ButtonStyle.success)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid == self.turno_uid:
            await interaction.response.send_message("Vos pusiste la frase, no podés votar.", ephemeral=True)
            return
        if uid not in self.partida.jugadores_map:
            await interaction.response.send_message("No estás en esta partida.", ephemeral=True)
            return
        if uid in self.votos_si or uid in self.votos_no:
            await interaction.response.send_message("Ya votaste.", ephemeral=True)
            return
        self.votos_no.append(uid)
        await interaction.response.send_message("🙅 ¡Registrado!", ephemeral=True)
        if len(self.votos_si) + len(self.votos_no) >= len(self.pueden_votar) and not self._terminado:
            self._terminado = True
            self.stop()

    async def on_timeout(self):
        if not self._terminado:
            self._terminado = True
            self.stop()

# ─── LÓGICA ───────────────────────────────────────────────
async def siguiente_ronda(partida):
    if partida.canal.id not in partidas_nn:
        return

    turno     = partida.jugador_turno()
    ronda_num = partida.ronda_actual + 1
    total     = partida.total_rondas()

    embed = discord.Embed(
        title=f"🎮 Nunca Nunca — Ronda {ronda_num}/{total}",
        description=f"Le toca a **{turno['nombre']}** poner una frase.\n{turno['member'].mention} presioná el botón para escribirla (solo vos la ves antes de publicarla).",
        color=COLOR
    )
    embed.set_footer(text="Tenés 2 minutos para escribir tu frase")

    ranking  = sorted(partida.jugadores, key=lambda x: x["veces"], reverse=True)
    marcador = "\n".join([f"**{j['nombre']}**: {j['veces']} veces" for j in ranking])
    embed.add_field(name="📊 Marcador actual", value=marcador, inline=False)

    await partida.canal.send(
        content=turno["member"].mention,
        embed=embed,
        view=VistaEscribirFrase(partida)
    )

async def mostrar_votacion(partida, frase, mensaje):
    turno = partida.jugador_turno()

    embed = discord.Embed(
        title=f"🎮 Nunca Nunca — Ronda {partida.ronda_actual + 1}/{partida.total_rondas()}",
        description=f"## {frase}",
        color=COLOR
    )
    embed.set_footer(text="Tenés 30 segundos para votar | El que puso la frase no vota")

    vista    = VistaVotoNunca(partida, frase)
    msg_voto = await partida.canal.send(embed=embed, view=vista)
    await vista.wait()

    si_nombres = [partida.jugadores_map[uid]["nombre"] for uid in vista.votos_si]
    no_nombres = [partida.jugadores_map[uid]["nombre"] for uid in vista.votos_no]
    no_votaron = [j["nombre"] for j in partida.jugadores
                  if j["uid"] != turno["uid"]
                  and j["uid"] not in vista.votos_si
                  and j["uid"] not in vista.votos_no]

    embed_res = discord.Embed(
        title=f"📊 Resultado — Ronda {partida.ronda_actual + 1}",
        description=f"*{frase}*",
        color=COLOR
    )
    embed_res.add_field(name="✋ Lo hicieron",       value=", ".join(si_nombres) if si_nombres else "Nadie", inline=False)
    embed_res.add_field(name="🙅 Nunca lo hicieron", value=", ".join(no_nombres) if no_nombres else "Nadie", inline=False)
    if no_votaron:
        embed_res.add_field(name="⏱️ No votaron", value=", ".join(no_votaron), inline=False)

    ranking  = sorted(partida.jugadores, key=lambda x: x["veces"], reverse=True)
    marcador = "\n".join([f"**{j['nombre']}**: {j['veces']} veces" for j in ranking])
    embed_res.add_field(name="📈 Marcador", value=marcador, inline=False)

    await msg_voto.edit(view=None)
    await partida.canal.send(embed=embed_res)

    partida.ronda_actual += 1
    await asyncio.sleep(4)

    if partida.ronda_actual >= partida.total_rondas():
        await mostrar_resultado_final(partida)
    else:
        await siguiente_ronda(partida)

async def mostrar_resultado_final(partida):
    ranking = sorted(partida.jugadores, key=lambda x: x["veces"], reverse=True)
    embed   = discord.Embed(title="🏆 ¡Fin del Nunca Nunca!", color=COLOR_WIN)
    medallas = ["🥇", "🥈", "🥉"]
    desc = "\n".join([
        f"{medallas[i] if i < 3 else f'#{i+1}'} **{j['nombre']}** — {j['veces']} veces"
        for i, j in enumerate(ranking)
    ])
    embed.description = desc
    perdedor = ranking[0]
    inocente = ranking[-1]
    embed.add_field(name="😂 El más veterano", value=f"**{perdedor['nombre']}** lo hizo {perdedor['veces']} veces", inline=False)
    embed.add_field(name="😇 El más inocente", value=f"**{inocente['nombre']}** solo {inocente['veces']} veces",   inline=False)
    await partida.canal.send(embed=embed)
    partidas_nn.pop(partida.canal.id, None)

# ─── COG ──────────────────────────────────────────────────
class NuncaNunca(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.group(name="nunca", invoke_without_command=True)
    async def nunca(self, ctx):
        embed = discord.Embed(title="🎮 Nunca Nunca — Ayuda", color=COLOR)
        embed.add_field(name="$nunca crear [max jugadores]", value="Crea una sala. Máx jugadores entre 5 y 10.\nEjemplo: `$nunca crear 6`", inline=False)
        embed.add_field(name="Cómo se juega", value="Cada jugador pone una frase de 'Nunca nunca...' en su turno.\nLos demás votan si lo hicieron o no.\nEl que más veces lo hizo pierde.", inline=False)
        embed.add_field(name="$nunca terminar", value="Termina la partida (solo admins).", inline=False)
        await ctx.send(embed=embed)

    @nunca.command(name="crear")
    async def crear(self, ctx, max_jugadores: int = 6):
        if ctx.channel.id in partidas_nn:
            await ctx.send(embed=discord.Embed(description="❌ Ya hay una partida en este canal.", color=COLOR_ERROR))
            return
        if not (5 <= max_jugadores <= 10):
            await ctx.send(embed=discord.Embed(description="❌ El máximo de jugadores debe estar entre 5 y 10.", color=COLOR_ERROR))
            return

        partida       = PartidaNuncaNunca(ctx.channel, ctx.author, max_jugadores)
        datos_creador = {"uid": ctx.author.id, "nombre": ctx.author.display_name, "member": ctx.author, "veces": 0}
        partida.jugadores.append(datos_creador)
        partida.jugadores_map[ctx.author.id] = datos_creador
        partidas_nn[ctx.channel.id] = partida

        embed = discord.Embed(
            title="🎮 Nunca Nunca",
            description="Cada jugador pone su frase en su turno. Los demás votan si lo hicieron.\n¡El más veterano pierde!",
            color=COLOR
        )
        embed.add_field(name="👥 Máx jugadores", value=str(max_jugadores), inline=True)
        embed.add_field(name=f"Jugadores (1/{max_jugadores})", value=ctx.author.display_name, inline=False)
        embed.set_footer(text="El creador inicia cuando estén todos | Las rondas = cantidad de jugadores")
        await ctx.send(embed=embed, view=VistaSalaNunca(partida))

    @nunca.command(name="terminar")
    @commands.has_permissions(administrator=True)
    async def terminar(self, ctx):
        if ctx.channel.id not in partidas_nn:
            await ctx.send(embed=discord.Embed(description="❌ No hay partida activa.", color=COLOR_ERROR))
            return
        del partidas_nn[ctx.channel.id]
        await ctx.send(embed=discord.Embed(description="✅ Partida terminada.", color=COLOR))

async def setup(bot):
    await bot.add_cog(NuncaNunca(bot))