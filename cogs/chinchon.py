import discord
from discord.ext import commands
import random
import asyncio
from itertools import combinations

COLOR       = discord.Color.gold()
COLOR_ERROR = discord.Color.red()
COLOR_WIN   = discord.Color.green()

# ─── BARAJA ESPAÑOLA ──────────────────────────────────────
PALOS   = ["🪙 Oros", "🏆 Copas", "⚔️ Espadas", "🍺 Bastos"]
VALORES = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]  # sin 8 y 9 en baraja española
NOMBRES = {1:"As", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7",
           10:"Sota", 11:"Caballo", 12:"Rey"}
# Puntos de cada carta (As=1, 2-7 val propio, Sota=10, Caballo=11, Rey=12... para puntaje)
PUNTOS_CARTA = {1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:7, 10:10, 11:11, 12:12}

def crear_baraja():
    b = [{"palo": p, "valor": v} for p in PALOS for v in VALORES]
    random.shuffle(b)
    return b

def nombre_carta(c):
    return f"{NOMBRES[c['valor']]} de {c['palo']}"

def emoji_carta(c):
    return f"`{NOMBRES[c['valor']]:6s}` {c['palo']}"

def puntos_carta(c):
    return PUNTOS_CARTA[c["valor"]]

# ─── DETECCIÓN DE GRUPOS Y ESCALERAS ──────────────────────
def es_escalera(cartas):
    """3+ cartas del mismo palo con valores consecutivos."""
    if len(cartas) < 3: return False
    palos = set(c["palo"] for c in cartas)
    if len(palos) != 1: return False
    vals = sorted(c["valor"] for c in cartas)
    # Valores reales en la baraja (sin 8 y 9)
    orden = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
    idxs  = [orden.index(v) for v in vals if v in orden]
    if len(idxs) != len(vals): return False
    idxs.sort()
    return all(idxs[i+1] - idxs[i] == 1 for i in range(len(idxs)-1))

def es_grupo(cartas):
    """3-4 cartas del mismo valor."""
    if len(cartas) < 3: return False
    return len(set(c["valor"] for c in cartas)) == 1

def calcular_puntaje_mano(mano):
    """Calcula el mínimo puntaje posible de la mano (cartas no agrupables)."""
    n = len(mano)
    mejor_resta = 0  # máximo que podemos "salvar" (agrupar)

    # Probar todas las combinaciones de 3 y 4 cartas
    for tam in [4, 3]:
        for combo in combinations(range(n), tam):
            subset = [mano[i] for i in combo]
            if es_escalera(subset) or es_grupo(subset):
                pts = sum(puntos_carta(c) for c in subset)
                if pts > mejor_resta:
                    mejor_resta = pts

    total = sum(puntos_carta(c) for c in mano)
    return total - mejor_resta

def encontrar_combinaciones(mano):
    """Devuelve lista de grupos/escaleras encontrados."""
    n = len(mano)
    encontrados = []
    usados = set()

    for tam in [4, 3]:
        for combo in combinations(range(n), tam):
            if any(i in usados for i in combo): continue
            subset = [mano[i] for i in combo]
            if es_escalera(subset) or es_grupo(subset):
                tipo = "Escalera" if es_escalera(subset) else "Grupo"
                encontrados.append({"indices": combo, "cartas": subset, "tipo": tipo})
                for i in combo: usados.add(i)

    return encontrados

def es_chinchon(mano):
    """Todas las cartas forman una escalera del mismo palo."""
    if len(mano) != 7: return False
    return es_escalera(mano)

# ─── PARTIDA ──────────────────────────────────────────────
class JugadorChinchon:
    def __init__(self, member):
        self.member  = member
        self.uid     = member.id
        self.nombre  = member.display_name
        self.mano:   list = []
        self.puntos  = 0   # acumulado de rondas
        self.eliminado = False

class PartidaChinchon:
    def __init__(self, canal_origen, creador, limite_puntos):
        self.canal_origen  = canal_origen
        self.canal         = None
        self.creador       = creador
        self.limite_puntos = limite_puntos
        self.jugadores:    list[JugadorChinchon] = []
        self.jugadores_map: dict = {}
        self.mazo:         list = []
        self.descarte:     list = []
        self.turno_idx     = 0
        self.ronda         = 0
        self.en_curso      = False

    def jugador_turno(self): return self.jugadores[self.turno_idx]
    def siguiente_turno(self):
        activos = [j for j in self.jugadores if not j.eliminado]
        idx_actual = activos.index(self.jugador_turno()) if self.jugador_turno() in activos else 0
        self.turno_idx = self.jugadores.index(activos[(idx_actual + 1) % len(activos)])

    def activos(self):
        return [j for j in self.jugadores if not j.eliminado]

partidas_ch: dict = {}

# ─── CANAL TEMPORAL ───────────────────────────────────────
async def crear_canal_temporal(guild, nombre, members, categoria=None):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }
    for m in members:
        overwrites[m] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    try:
        return await guild.create_text_channel(
            nombre, category=categoria, overwrites=overwrites,
            topic="🃏 Canal temporal de Chinchón — Se elimina al terminar."
        )
    except discord.Forbidden:
        return None

async def eliminar_canal_temporal(canal, delay=15):
    await asyncio.sleep(delay)
    try: await canal.delete(reason="Partida de Chinchón finalizada")
    except: pass

# ─── VISTA SALA ───────────────────────────────────────────
class VistaSalaChinchon(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=300)
        self.partida = partida

    async def on_timeout(self):
        partidas_ch.pop(self.partida.canal_origen.id, None)

    @discord.ui.button(label="✅ Unirse", style=discord.ButtonStyle.success)
    async def unirse(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid in self.partida.jugadores_map:
            await interaction.response.send_message("Ya estás en la partida.", ephemeral=True); return
        if len(self.partida.jugadores) >= 4:
            await interaction.response.send_message("Máximo 4 jugadores.", ephemeral=True); return

        j = JugadorChinchon(interaction.user)
        self.partida.jugadores.append(j)
        self.partida.jugadores_map[uid] = j

        nombres = ", ".join(j.nombre for j in self.partida.jugadores)
        emb = interaction.message.embeds[0]
        emb.set_field_at(1, name=f"Jugadores ({len(self.partida.jugadores)}/4)", value=nombres)
        await interaction.message.edit(embed=emb)
        await interaction.response.send_message("✅ ¡Te uniste!", ephemeral=True)

    @discord.ui.button(label="🚀 Iniciar", style=discord.ButtonStyle.primary)
    async def iniciar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.partida.creador.id:
            await interaction.response.send_message("Solo el creador puede iniciar.", ephemeral=True); return
        if len(self.partida.jugadores) < 2:
            await interaction.response.send_message("Necesitás al menos 2 jugadores.", ephemeral=True); return
        self.stop()
        await interaction.message.edit(view=None)
        await interaction.response.send_message("🚀 ¡Arrancamos!", ephemeral=True)
        await iniciar_chinchon(self.partida, interaction.guild, interaction.message)

    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.danger)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.partida.creador.id:
            await interaction.response.send_message("Solo el creador puede cancelar.", ephemeral=True); return
        self.stop()
        partidas_ch.pop(self.partida.canal_origen.id, None)
        await interaction.message.edit(content="❌ Sala cancelada.", embed=None, view=None)
        await interaction.response.send_message("Cancelado.", ephemeral=True)

# ─── VISTA TURNO ──────────────────────────────────────────
class VistaTurnoChinchon(discord.ui.View):
    def __init__(self, partida):
        super().__init__(timeout=120)
        self.partida  = partida
        self._accion  = False

    async def on_timeout(self):
        if not self._accion:
            self._accion = True
            self.stop()
            j = self.partida.jugador_turno()
            carta = self.partida.mazo.pop()
            j.mano.append(carta)
            await self.partida.canal.send(
                embed=discord.Embed(
                    description=f"⏱️ **{j.nombre}** tardó demasiado. Robó del mazo automáticamente.",
                    color=COLOR_ERROR
                )
            )
            await pedir_descarte(self.partida, j)

    @discord.ui.button(label="👁️ Ver mi mano", style=discord.ButtonStyle.secondary, row=0)
    async def ver_mano(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.partida.jugadores_map:
            await interaction.response.send_message("No estás en esta partida.", ephemeral=True); return
        j = self.partida.jugadores_map[interaction.user.id]
        await interaction.response.send_message(embed=_build_embed_mano(j), ephemeral=True)

    @discord.ui.button(label="🃏 Robar del mazo",      style=discord.ButtonStyle.primary,  row=1)
    async def robar_mazo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await _verificar_turno(interaction, self.partida): return
        if self._accion:
            await interaction.response.send_message("Ya tomaste una acción.", ephemeral=True); return
        self._accion = True
        self.stop()
        j     = self.partida.jugador_turno()
        carta = self.partida.mazo.pop()
        j.mano.append(carta)
        await interaction.response.send_message(
            embed=discord.Embed(description=f"🃏 Robaste: **{nombre_carta(carta)}**\n\nTu mano ahora tiene {len(j.mano)} cartas.", color=COLOR),
            ephemeral=True
        )
        await interaction.message.edit(view=None)
        await pedir_descarte(self.partida, j)

    @discord.ui.button(label="♻️ Tomar del descarte", style=discord.ButtonStyle.secondary, row=1)
    async def robar_descarte(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await _verificar_turno(interaction, self.partida): return
        if self._accion:
            await interaction.response.send_message("Ya tomaste una acción.", ephemeral=True); return
        if not self.partida.descarte:
            await interaction.response.send_message("El descarte está vacío.", ephemeral=True); return
        self._accion = True
        self.stop()
        j     = self.partida.jugador_turno()
        carta = self.partida.descarte.pop()
        j.mano.append(carta)
        await interaction.response.send_message(
            embed=discord.Embed(description=f"♻️ Tomaste del descarte: **{nombre_carta(carta)}**\n\nTu mano ahora tiene {len(j.mano)} cartas.", color=COLOR),
            ephemeral=True
        )
        await interaction.message.edit(view=None)
        await pedir_descarte(self.partida, j)

async def _verificar_turno(interaction, partida):
    if interaction.user.id != partida.jugador_turno().uid:
        await interaction.response.send_message("No es tu turno.", ephemeral=True)
        return False
    return True

# ─── VISTA DESCARTE ───────────────────────────────────────
class VistaDescarte(discord.ui.View):
    def __init__(self, partida, jugador):
        super().__init__(timeout=120)
        self.partida  = partida
        self.jugador  = jugador
        self._accion  = False
        self._build()

    def _build(self):
        for i, carta in enumerate(self.jugador.mano):
            btn = discord.ui.Button(
                label=f"{NOMBRES[carta['valor']]} {carta['palo']}",
                style=discord.ButtonStyle.secondary,
                row=i // 4
            )
            btn.callback = self._descartar(i)
            self.add_item(btn)

        # Botón ver mano (ephemeral)
        btn_ver = discord.ui.Button(
            label="👁️ Ver mi mano",
            style=discord.ButtonStyle.primary,
            row=2
        )
        btn_ver.callback = self._ver_mano
        self.add_item(btn_ver)

        # Botón bajar (cerrar la ronda)
        btn_bajar = discord.ui.Button(
            label="📥 Bajar (cerrar ronda)",
            style=discord.ButtonStyle.success,
            row=2
        )
        btn_bajar.callback = self._bajar
        self.add_item(btn_bajar)

    async def _ver_mano(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.partida.jugadores_map:
            await interaction.response.send_message("No estás en esta partida.", ephemeral=True); return
        j = self.partida.jugadores_map[interaction.user.id]
        await interaction.response.send_message(embed=_build_embed_mano(j), ephemeral=True)

    def _descartar(self, idx):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.jugador.uid:
                await interaction.response.send_message("No es tu turno.", ephemeral=True); return
            if self._accion: return
            self._accion = True
            self.stop()

            carta = self.jugador.mano.pop(idx)
            self.partida.descarte.append(carta)

            await interaction.response.send_message(
                embed=discord.Embed(description=f"🗑️ Descartaste: **{nombre_carta(carta)}**", color=COLOR),
                ephemeral=True
            )
            await interaction.message.edit(view=None)
            await siguiente_turno_chinchon(self.partida)
        return callback

    async def _bajar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.jugador.uid:
            await interaction.response.send_message("No es tu turno.", ephemeral=True); return
        if self._accion: return

        # Verificar si puede bajar (tiene combinaciones o chinchón)
        combos = encontrar_combinaciones(self.jugador.mano)
        cartas_en_combo = sum(len(c["indices"]) for c in combos)
        sobrantes = len(self.jugador.mano) - cartas_en_combo

        if sobrantes > 1:
            pts_restantes = sum(puntos_carta(self.jugador.mano[i])
                                for i in range(len(self.jugador.mano))
                                if not any(i in c["indices"] for c in combos))
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"❌ Para bajar necesitás que te quede **máximo 1 carta suelta**.\nActualmente tenés **{sobrantes} cartas sueltas** ({pts_restantes} pts).\nDescartá una carta primero.",
                    color=COLOR_ERROR
                ),
                ephemeral=True
            )
            return

        self._accion = True
        self.stop()
        await interaction.response.defer()
        await interaction.message.edit(view=None)
        await cerrar_ronda(self.partida, self.jugador, combos)

    async def on_timeout(self):
        if not self._accion:
            self._accion = True
            self.stop()
            # Descartar carta aleatoria automáticamente
            if self.jugador.mano:
                carta = self.jugador.mano.pop(random.randint(0, len(self.jugador.mano)-1))
                self.partida.descarte.append(carta)
                await self.partida.canal.send(
                    embed=discord.Embed(
                        description=f"⏱️ **{self.jugador.nombre}** tardó demasiado. Se descartó **{nombre_carta(carta)}** automáticamente.",
                        color=COLOR_ERROR
                    )
                )
            await siguiente_turno_chinchon(self.partida)

# ─── LÓGICA PRINCIPAL ─────────────────────────────────────
async def iniciar_chinchon(partida, guild, msg_sala):
    members = [j.member for j in partida.jugadores]
    canal_temp = await crear_canal_temporal(
        guild, f"chinchon-{partida.canal_origen.name[:15]}",
        members, partida.canal_origen.category
    )
    if canal_temp:
        partida.canal = canal_temp
        await msg_sala.edit(embed=discord.Embed(
            title="🃏 Chinchón iniciado",
            description=f"La partida se movió a {canal_temp.mention}\n¡Entren ahí para jugar!",
            color=COLOR
        ))
    else:
        partida.canal = partida.canal_origen
        await msg_sala.edit(embed=discord.Embed(
            description="⚠️ Sin permisos para crear canal. Jugando acá.",
            color=COLOR_ERROR
        ))

    await nueva_ronda(partida)

async def nueva_ronda(partida):
    if partida.canal_origen.id not in partidas_ch: return
    partida.ronda += 1
    partida.mazo     = crear_baraja()
    partida.descarte = []

    # Repartir 7 cartas a cada jugador activo
    for j in partida.activos():
        j.mano = [partida.mazo.pop() for _ in range(7)]

    # Primera carta al descarte
    partida.descarte.append(partida.mazo.pop())

    activos_txt = "\n".join(f"• **{j.nombre}**" for j in partida.activos())
    emb = discord.Embed(
        title=f"🃏 Chinchón — Ronda {partida.ronda}",
        description=f"Se repartieron 7 cartas a cada jugador.\n{activos_txt}",
        color=COLOR
    )
    emb.add_field(name="🃏 Descarte inicial", value=nombre_carta(partida.descarte[-1]), inline=True)
    emb.add_field(name="🎯 Límite", value=f"{partida.limite_puntos} puntos para perder", inline=True)

    # Ranking actual
    rank_txt = "\n".join(f"**{j.nombre}**: {j.puntos} pts" for j in partida.jugadores)
    emb.add_field(name="📊 Puntos acumulados", value=rank_txt, inline=False)
    emb.set_footer(text="El que llega al límite de puntos queda eliminado")

    await partida.canal.send(embed=emb)
    await asyncio.sleep(2)
    await turno_chinchon(partida)

async def turno_chinchon(partida):
    if partida.canal_origen.id not in partidas_ch: return

    j      = partida.jugador_turno()
    tope   = partida.descarte[-1] if partida.descarte else None
    n_mazo = len(partida.mazo)

    emb = discord.Embed(
        title=f"🃏 Turno de {j.nombre}",
        description=f"Tocá un botón para robar una carta.",
        color=COLOR
    )
    emb.add_field(
        name="🗑️ Tope del descarte",
        value=nombre_carta(tope) if tope else "Vacío",
        inline=True
    )
    emb.add_field(name="🃏 Mazo", value=f"{n_mazo} cartas", inline=True)

    # Mostrar mano solo al jugador con ephemeral hint
    mano_txt = "\n".join(f"{i+1}. {nombre_carta(c)}" for i, c in enumerate(j.mano))
    emb.add_field(name=f"🤫 Tu mano (visible solo para vos)", value="Usá el botón para ver tus cartas", inline=False)
    emb.set_footer(text=f"Tenés 2 minutos para elegir")

    vista = VistaTurnoChinchon(partida)
    await partida.canal.send(content=j.member.mention, embed=emb, view=vista)
    await vista.wait()

def _build_embed_mano(jugador):
    mano_txt = "\n".join(f"`{i+1}.` {emoji_carta(c)}" for i, c in enumerate(jugador.mano))
    combos   = encontrar_combinaciones(jugador.mano)
    pts_mano = calcular_puntaje_mano(jugador.mano)

    combos_txt = ""
    if combos:
        for c in combos:
            cartas_str = ", ".join(nombre_carta(x) for x in c["cartas"])
            combos_txt += f"\n✅ {c['tipo']}: {cartas_str}"
    else:
        combos_txt = "Ninguna combinación aún"

    emb = discord.Embed(title=f"🃏 Tu mano — {jugador.nombre}", color=COLOR)
    emb.add_field(name="Cartas", value=mano_txt, inline=False)
    emb.add_field(name="🔗 Combinaciones detectadas", value=combos_txt, inline=False)
    emb.add_field(name="📊 Puntos si bajás ahora", value=f"**{pts_mano} pts**", inline=True)
    emb.set_footer(text="👁️ Solo vos ves este mensaje")
    return emb

async def pedir_descarte(partida, jugador):
    """Después de robar, mostrar mano actualizada y pedir que descarte."""
    if partida.canal_origen.id not in partidas_ch: return

    mano_txt = "\n".join(f"`{i+1}.` {emoji_carta(c)}" for i, c in enumerate(jugador.mano))
    combos   = encontrar_combinaciones(jugador.mano)
    pts_mano = calcular_puntaje_mano(jugador.mano)

    combos_txt = ""
    if combos:
        for c in combos:
            cartas_str = ", ".join(nombre_carta(x) for x in c["cartas"])
            combos_txt += f"\n✅ {c['tipo']}: {cartas_str}"

    emb = discord.Embed(
        title=f"🗑️ {jugador.nombre} — Elegí qué descartar",
        description="Seleccioná una carta para descartar, o bajá si podés cerrar la ronda.",
        color=COLOR
    )
    emb.add_field(name="Tu mano (8 cartas)", value=mano_txt, inline=False)
    if combos_txt:
        emb.add_field(name="🔗 Combinaciones", value=combos_txt, inline=False)
    emb.add_field(name="📊 Puntos si bajás", value=f"**{pts_mano} pts**", inline=True)

    vista = VistaDescarte(partida, jugador)
    await partida.canal.send(content=jugador.member.mention, embed=emb, view=vista)
    await vista.wait()

async def siguiente_turno_chinchon(partida):
    if partida.canal_origen.id not in partidas_ch: return

    # Reponer mazo si se agotó
    if not partida.mazo:
        tope = partida.descarte.pop()
        partida.mazo = partida.descarte[:]
        partida.descarte = [tope]
        random.shuffle(partida.mazo)
        await partida.canal.send(
            embed=discord.Embed(description="🔄 El mazo se agotó. Se barajó el descarte.", color=COLOR)
        )

    partida.siguiente_turno()
    await asyncio.sleep(1)
    await turno_chinchon(partida)

async def cerrar_ronda(partida, ganador_ronda, combos_ganador):
    """El jugador que bajó cierra la ronda. Se calculan puntos."""
    if partida.canal_origen.id not in partidas_ch: return

    # Verificar chinchón
    chinchon = es_chinchon(ganador_ronda.mano)

    emb = discord.Embed(
        title=f"📥 {'🎉 ¡CHINCHÓN!' if chinchon else '¡Ronda cerrada!'} — Cerró {ganador_ronda.nombre}",
        color=COLOR_WIN
    )

    if chinchon:
        emb.description = f"**{ganador_ronda.nombre}** hizo **CHINCHÓN** — gana la partida directamente!"
        await partida.canal.send(embed=emb)
        await fin_partida(partida, ganador_ronda, chinchon=True)
        return

    # Mostrar manos de todos y calcular puntos
    resultados = []
    for j in partida.activos():
        pts = calcular_puntaje_mano(j.mano)
        combos = encontrar_combinaciones(j.mano)
        cartas_str = ", ".join(nombre_carta(c) for c in j.mano)

        if j.uid == ganador_ronda.uid:
            pts = 0  # quien cierra suma 0 (o los puntos restantes si tiene 1 carta suelta)
            sobrantes = [j.mano[i] for i in range(len(j.mano)) if not any(i in c["indices"] for c in combos_ganador)]
            pts = sum(puntos_carta(c) for c in sobrantes)

        j.puntos += pts
        resultados.append((j, pts, cartas_str))
        emb.add_field(
            name=f"{'✅' if j.uid == ganador_ronda.uid else '🃏'} {j.nombre} — +{pts} pts (total: {j.puntos})",
            value=cartas_str[:100],
            inline=False
        )

    await partida.canal.send(embed=emb)

    # Eliminar jugadores que superaron el límite
    eliminados = []
    for j in partida.activos():
        if j.puntos >= partida.limite_puntos:
            j.eliminado = True
            eliminados.append(j)

    if eliminados:
        txt = ", ".join(f"**{j.nombre}** ({j.puntos} pts)" for j in eliminados)
        await partida.canal.send(
            embed=discord.Embed(description=f"💀 Eliminados: {txt}", color=COLOR_ERROR)
        )

    activos = partida.activos()
    if len(activos) == 1:
        await fin_partida(partida, activos[0])
        return
    if len(activos) == 0:
        # Edge case: todos eliminados a la vez
        ganador = min(partida.jugadores, key=lambda x: x.puntos)
        await fin_partida(partida, ganador)
        return

    await asyncio.sleep(4)
    await nueva_ronda(partida)

async def fin_partida(partida, ganador, chinchon=False):
    ranking = sorted(partida.jugadores, key=lambda x: x.puntos)
    medallas = ["🥇","🥈","🥉","4️⃣"]
    desc = "\n".join(
        f"{medallas[i]} **{j.nombre}** — {j.puntos} pts {'💀' if j.eliminado else ''}"
        for i, j in enumerate(ranking)
    )
    emb = discord.Embed(
        title=f"🏆 {'¡CHINCHÓN!' if chinchon else '¡Fin del Chinchón!'}",
        color=COLOR_WIN
    )
    emb.description = desc
    emb.add_field(
        name="🎉 Ganador",
        value=f"**{ganador.nombre}**" + (" con CHINCHÓN 🃏🎉" if chinchon else ""),
        inline=False
    )
    emb.set_footer(text="Este canal se eliminará en 15 segundos")
    await partida.canal.send(embed=emb)

    partidas_ch.pop(partida.canal_origen.id, None)
    if partida.canal and partida.canal != partida.canal_origen:
        asyncio.create_task(eliminar_canal_temporal(partida.canal, delay=15))

# ─── COG ──────────────────────────────────────────────────
class Chinchon(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.group(name="chinchon", aliases=["ch"], invoke_without_command=True)
    async def chinchon(self, ctx):
        emb = discord.Embed(title="🃏 Chinchón — Ayuda", color=COLOR)
        emb.add_field(name="$ch crear [límite]", value="Crea una sala. Límite = puntos para quedar eliminado.\nEjemplo: `$ch crear 100`\nDefault: 100 puntos.", inline=False)
        emb.add_field(name="Reglas",
            value=(
                "• 2-4 jugadores, baraja española de 40 cartas\n"
                "• Cada turno: robás del mazo o del descarte, y descartás una carta\n"
                "• Objetivo: formar **escaleras** (mismo palo, consecutivas) o **grupos** (mismo número)\n"
                "• **Bajar**: cuando te queda 1 carta suelta o menos, podés cerrar la ronda\n"
                "• **Chinchón**: si las 7 cartas forman una escalera — ganás instantáneamente\n"
                "• Al cerrar, todos suman los puntos de sus cartas no agrupadas\n"
                "• Al llegar al límite de puntos, quedás eliminado"
            ), inline=False)
        emb.add_field(name="$ch terminar", value="Termina la partida (solo admins).", inline=False)
        await ctx.send(embed=emb)

    @chinchon.command(name="crear")
    async def crear(self, ctx, limite: int = 100):
        if ctx.channel.id in partidas_ch:
            await ctx.send(embed=discord.Embed(description="❌ Ya hay una partida en este canal.", color=COLOR_ERROR)); return
        if not (50 <= limite <= 200):
            await ctx.send(embed=discord.Embed(description="❌ El límite debe estar entre 50 y 200.", color=COLOR_ERROR)); return

        partida = PartidaChinchon(ctx.channel, ctx.author, limite)
        j = JugadorChinchon(ctx.author)
        partida.jugadores.append(j)
        partida.jugadores_map[ctx.author.id] = j
        partidas_ch[ctx.channel.id] = partida

        emb = discord.Embed(
            title="🃏 Sala de Chinchón",
            description="Baraja española, 2-4 jugadores. ¡El que menos puntos acumule gana!",
            color=COLOR
        )
        emb.add_field(name="🎯 Límite de puntos", value=str(limite), inline=True)
        emb.add_field(name=f"Jugadores (1/4)", value=ctx.author.display_name, inline=False)
        emb.set_footer(text="El creador inicia cuando estén todos | Se creará un canal privado al iniciar")
        await ctx.send(embed=emb, view=VistaSalaChinchon(partida))

    @chinchon.command(name="terminar")
    @commands.has_permissions(administrator=True)
    async def terminar(self, ctx):
        if ctx.channel.id not in partidas_ch:
            await ctx.send(embed=discord.Embed(description="❌ No hay partida activa.", color=COLOR_ERROR)); return
        partida = partidas_ch.pop(ctx.channel.id)
        await ctx.send(embed=discord.Embed(description="✅ Partida terminada.", color=COLOR))
        if partida.canal and partida.canal != partida.canal_origen:
            asyncio.create_task(eliminar_canal_temporal(partida.canal, delay=5))

async def setup(bot):
    await bot.add_cog(Chinchon(bot))