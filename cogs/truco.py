import discord
from discord.ext import commands
import random
import asyncio

COLOR = discord.Color.gold()
COLOR_ERROR = discord.Color.red()
COLOR_WIN = discord.Color.green()

PALOS = ["espadas", "bastos", "copas", "oros"]
NUMEROS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]

PALO_EMOJI = {"espadas": "⚔️", "bastos": "🪵", "copas": "🏆", "oros": "🪙"}
NUMERO_NOMBRE = {1:"1",2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",10:"10",11:"11",12:"12"}

PODER_TRUCO = {
    (1,"espadas"):14,(1,"bastos"):13,(7,"espadas"):12,(7,"oros"):11,
    (3,"espadas"):10,(3,"bastos"):10,(3,"copas"):10,(3,"oros"):10,
    (2,"espadas"):9,(2,"bastos"):9,(2,"copas"):9,(2,"oros"):9,
    (1,"copas"):8,(1,"oros"):8,
    (12,"espadas"):7,(12,"bastos"):7,(12,"copas"):7,(12,"oros"):7,
    (11,"espadas"):6,(11,"bastos"):6,(11,"copas"):6,(11,"oros"):6,
    (10,"espadas"):5,(10,"bastos"):5,(10,"copas"):5,(10,"oros"):5,
    (7,"copas"):4,(7,"bastos"):4,
    (6,"espadas"):3,(6,"bastos"):3,(6,"copas"):3,(6,"oros"):3,
    (5,"espadas"):2,(5,"bastos"):2,(5,"copas"):2,(5,"oros"):2,
    (4,"espadas"):1,(4,"bastos"):1,(4,"copas"):1,(4,"oros"):1,
}

def valor_envido(carta): return 0 if carta[0]>=10 else carta[0]
def calcular_envido(cartas):
    por_palo={}
    for c in cartas: por_palo.setdefault(c[1],[]).append(c)
    mejor=0
    for cs in por_palo.values():
        if len(cs)>=2:
            vals=sorted([valor_envido(c) for c in cs],reverse=True)
            mejor=max(mejor,20+vals[0]+vals[1])
        else: mejor=max(mejor,valor_envido(cs[0]))
    return mejor
def tiene_flor(cartas): return len(set(c[1] for c in cartas))==1
def calcular_flor(cartas):
    vals=sorted([valor_envido(c) for c in cartas],reverse=True)
    return 20+vals[0]+vals[1]
def carta_str(carta): return f"{NUMERO_NOMBRE[carta[0]]} de {carta[1]} {PALO_EMOJI[carta[1]]}"

class Jugador:
    def __init__(self,member):
        self.member=member; self.cartas=[]; self.cartas_jugadas=[]; self.equipo=None

class Partida:
    def __init__(self,canal_origen,modo,puntos_max,con_flor):
        self.canal_origen=canal_origen
        self.canal=None  # canal temporal, se asigna al iniciar
        self.modo=modo; self.puntos_max=puntos_max; self.con_flor=con_flor
        self.jugadores=[]; self.equipos={1:[],2:[]}
        self.turno_idx=0; self.puntos={1:0,2:0}; self.mano_idx=0
        self.cartas_mesa=[]; self.ronda_actual=0; self.ganador_rondas=[]
        self.estado_envido="ninguno"; self.envido_cantado_por=None; self.envido_resuelto=False
        self.estado_truco="ninguno"; self.truco_cantado_por=None; self.truco_resuelto=False
        self.puntos_truco_en_juego=1; self.esperando_respuesta=False

    def max_jugadores(self): return 2 if self.modo=="1v1" else 4
    def jugador_actual(self): return self.jugadores[self.turno_idx%len(self.jugadores)]
    def get_equipo(self,jugador):
        for eq,js in self.equipos.items():
            if jugador in js: return eq
        return None
    def get_equipo_contrario(self,j): eq=self.get_equipo(j); return 2 if eq==1 else 1
    def es_mismo_equipo(self,j1,j2): return self.get_equipo(j1)==self.get_equipo(j2)
    def siguiente_turno(self): self.turno_idx=(self.turno_idx+1)%len(self.jugadores)
    def repartir(self):
        mazo=[(n,p) for p in PALOS for n in NUMEROS]; random.shuffle(mazo)
        for i,j in enumerate(self.jugadores): j.cartas=mazo[i*3:(i+1)*3]; j.cartas_jugadas=[]
        self.cartas_mesa=[]; self.ronda_actual=0; self.ganador_rondas=[]
        self.estado_envido="ninguno"; self.estado_truco="ninguno"
        self.envido_resuelto=False; self.truco_resuelto=False
        self.puntos_truco_en_juego=1; self.envido_cantado_por=None
        self.truco_cantado_por=None; self.esperando_respuesta=False
        self.turno_idx=self.mano_idx
    def puntos_envido_en_juego(self):
        e=self.estado_envido
        if e=="envido": return 2
        if e=="envido_envido": return 4
        if e=="real_envido": return 3
        if e=="envido_real": return 5
        if e=="falta_envido": return self.puntos_max-min(self.puntos.values())
        return 1
    def puntos_truco(self):
        e=self.estado_truco
        if e=="truco": return 2
        if e=="retruco": return 3
        if e=="vale_cuatro": return 4
        return 1
    def ganador_ronda(self):
        if not self.cartas_mesa: return None
        mejor=-1; mejor_j=None; empate=False
        for jug,carta in self.cartas_mesa:
            p=PODER_TRUCO.get(carta,0)
            if p>mejor: mejor=p; mejor_j=jug; empate=False
            elif p==mejor: empate=True
        return "empate" if empate else mejor_j
    def ganador_mano_actual(self):
        victorias={1:0,2:0}
        for g in self.ganador_rondas:
            if g!="empate":
                eq=self.get_equipo(g)
                if eq: victorias[eq]+=1
        if victorias[1]>=2: return 1
        if victorias[2]>=2: return 2
        if len(self.ganador_rondas)==3:
            primera=self.ganador_rondas[0]
            if primera=="empate":
                segunda=self.ganador_rondas[1]
                if segunda=="empate": return self.get_equipo(self.jugadores[self.mano_idx])
                return self.get_equipo(segunda)
            return self.get_equipo(primera)
        return None

partidas_truco={}

# ─── CANAL TEMPORAL ───────────────────────────────────────
async def crear_canal_temporal(guild, nombre, jugadores, categoria=None):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }
    for j in jugadores:
        overwrites[j.member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    try:
        canal = await guild.create_text_channel(
            nombre,
            category=categoria,
            overwrites=overwrites,
            topic="Canal temporal de Truco 🃏 — Se eliminará al terminar la partida."
        )
        return canal
    except discord.Forbidden:
        return None

async def eliminar_canal_temporal(canal, delay=10):
    await asyncio.sleep(delay)
    try:
        await canal.delete(reason="Partida de Truco finalizada")
    except:
        pass

# ─── FUNCIONES DE JUEGO ───────────────────────────────────
def crear_embed_sala(partida):
    embed=discord.Embed(title="🃏 Sala de Truco",color=COLOR)
    embed.add_field(name="Modo",value=partida.modo,inline=True)
    embed.add_field(name="Puntos",value=f"Hasta {partida.puntos_max}",inline=True)
    embed.add_field(name="Flor",value="✅ Con Flor" if partida.con_flor else "❌ Sin Flor",inline=True)
    txt="".join([f"Equipo {partida.get_equipo(j)}: **{j.member.display_name}**\n" for j in partida.jugadores])
    embed.add_field(name=f"Jugadores ({len(partida.jugadores)}/{partida.max_jugadores()})",value=txt or "Esperando...",inline=False)
    embed.set_footer(text="✅ Unirse para entrar | El juego se moverá a un canal privado al iniciar")
    return embed

async def iniciar_partida(partida, mensaje_sala):
    guild = partida.canal_origen.guild
    nombre_canal = f"truco-{'x'.join([j.member.display_name[:4].lower() for j in partida.jugadores])}"
    categoria = partida.canal_origen.category

    canal_temp = await crear_canal_temporal(guild, nombre_canal, partida.jugadores, categoria)

    if canal_temp:
        partida.canal = canal_temp
        embed_info = discord.Embed(
            title="🃏 ¡Truco iniciado!",
            description=f"La partida se movió a {canal_temp.mention}\n¡Entren ahí para jugar!",
            color=COLOR
        )
        await mensaje_sala.edit(embed=embed_info, view=None)
    else:
        partida.canal = partida.canal_origen
        embed_info = discord.Embed(
            title="🃏 ¡Truco iniciado!",
            description="⚠️ No pude crear un canal temporal (falta permiso `Gestionar canales`). Jugando en este canal.",
            color=COLOR
        )
        await mensaje_sala.edit(embed=embed_info, view=None)

    embed = discord.Embed(title="🃏 ¡Comienza el Truco!", color=COLOR)
    for eq in [1,2]:
        nombres=[j.member.display_name for j in partida.equipos[eq]]
        embed.add_field(name=f"Equipo {eq}",value=", ".join(nombres) if nombres else "—")
    embed.set_footer(text="Las cartas son privadas — presioná '🃏 Ver mis cartas' para verlas")
    await partida.canal.send(embed=embed)
    await nueva_mano(partida)

async def nueva_mano(partida):
    for eq,pts in partida.puntos.items():
        if pts>=partida.puntos_max:
            nombres=[j.member.display_name for j in partida.equipos[eq]]
            embed=discord.Embed(title="🏆 ¡Fin del juego!",description=f"**Equipo {eq}** ({', '.join(nombres)}) ganó!",color=COLOR_WIN)
            embed.add_field(name="Marcador final",value=f"Equipo 1: **{partida.puntos[1]}** | Equipo 2: **{partida.puntos[2]}**")
            await partida.canal.send(embed=embed)
            partidas_truco.pop(partida.canal_origen.id, None)
            if partida.canal != partida.canal_origen:
                await partida.canal.send(embed=discord.Embed(description="🗑️ Este canal se eliminará en 15 segundos.", color=COLOR))
                asyncio.create_task(eliminar_canal_temporal(partida.canal, delay=15))
            return

    partida.repartir()
    mano=partida.jugadores[partida.mano_idx]
    embed=discord.Embed(title="🃏 Nueva mano",description=f"Marcador — Equipo 1: **{partida.puntos[1]}** | Equipo 2: **{partida.puntos[2]}**",color=COLOR)
    embed.add_field(name="El mano es",value=mano.member.display_name)
    embed.set_footer(text="Hacé click en '🃏 Ver mis cartas' para ver tus cartas (solo vos las ves)")
    await partida.canal.send(embed=embed,view=VistaVerCartas(partida))
    await asyncio.sleep(2)
    await mostrar_turno(partida)

async def mostrar_turno(partida):
    jugador=partida.jugador_actual()
    embed=discord.Embed(title=f"🎯 Turno de {jugador.member.display_name}",description=f"Marcador — Equipo 1: **{partida.puntos[1]}** | Equipo 2: **{partida.puntos[2]}**",color=COLOR)
    if partida.cartas_mesa:
        embed.add_field(name="🃏 Cartas en mesa",value="\n".join([f"**{j.member.display_name}**: {carta_str(c)}" for j,c in partida.cartas_mesa]),inline=False)
    if partida.estado_truco!="ninguno":
        embed.add_field(name="🎴 Truco",value=partida.estado_truco.upper(),inline=True)
    if partida.estado_envido!="ninguno" and not partida.envido_resuelto:
        embed.add_field(name="🎵 Envido",value=partida.estado_envido.upper(),inline=True)
    if partida.ganador_rondas:
        embed.add_field(name="Rondas",value="\n".join([f"Ronda {i+1}: {'Empate' if g=='empate' else g.member.display_name}" for i,g in enumerate(partida.ganador_rondas)]),inline=False)
    embed.set_footer(text=f"{jugador.member.display_name}: presioná '🎯 Ver mis opciones' para jugar")
    await partida.canal.send(content=jugador.member.mention,embed=embed,view=VistaTurno(partida,jugador))

async def resolver_ronda(partida):
    ganador=partida.ganador_ronda()
    partida.ganador_rondas.append(ganador)
    partida.cartas_mesa=[]; partida.ronda_actual+=1
    desc="🤝 Empate" if ganador=="empate" else f"🏅 **{ganador.member.display_name}** gana la ronda"
    await partida.canal.send(embed=discord.Embed(title=f"Ronda {partida.ronda_actual} — Resultado",description=desc,color=COLOR))
    ganador_eq=partida.ganador_mano_actual()
    if ganador_eq or partida.ronda_actual>=3:
        if ganador_eq is None: ganador_eq=partida.get_equipo(partida.jugadores[partida.mano_idx])
        pts=partida.puntos_truco_en_juego
        if partida.estado_truco in ["truco","retruco","vale_cuatro"] and not partida.truco_resuelto:
            pts=partida.puntos_truco()
        partida.puntos[ganador_eq]+=pts
        await partida.canal.send(embed=discord.Embed(title=f"🏆 Equipo {ganador_eq} gana la mano",description=f"+{pts} punto(s)\nMarcador — Equipo 1: **{partida.puntos[1]}** | Equipo 2: **{partida.puntos[2]}**",color=COLOR_WIN))
        partida.mano_idx=(partida.mano_idx+1)%len(partida.jugadores)
        await asyncio.sleep(2)
        await nueva_mano(partida)
    else:
        if ganador!="empate": partida.turno_idx=partida.jugadores.index(ganador)
        await mostrar_turno(partida)

# ─── VISTAS ───────────────────────────────────────────────
class VistaSala(discord.ui.View):
    def __init__(self,partida):
        super().__init__(timeout=300); self.partida=partida; self.mensaje=None

    @discord.ui.button(label="✅ Unirse",style=discord.ButtonStyle.success)
    async def unirse(self,interaction:discord.Interaction,button:discord.ui.Button):
        for j in self.partida.jugadores:
            if j.member.id==interaction.user.id:
                await interaction.response.send_message("Ya estás en la partida.",ephemeral=True); return
        if len(self.partida.jugadores)>=self.partida.max_jugadores():
            await interaction.response.send_message("La sala está llena.",ephemeral=True); return
        jugador=Jugador(interaction.user)
        idx=len(self.partida.jugadores)
        eq=idx+1 if self.partida.modo=="1v1" else (idx%2)+1
        jugador.equipo=eq; self.partida.jugadores.append(jugador); self.partida.equipos[eq].append(jugador)
        await interaction.response.send_message(f"✅ Te uniste al **Equipo {eq}**!",ephemeral=True)
        await interaction.message.edit(embed=crear_embed_sala(self.partida))
        if len(self.partida.jugadores)==self.partida.max_jugadores():
            self.stop()
            await iniciar_partida(self.partida, interaction.message)

    @discord.ui.button(label="❌ Cancelar",style=discord.ButtonStyle.danger)
    async def cancelar(self,interaction:discord.Interaction,button:discord.ui.Button):
        if not self.partida.jugadores or interaction.user.id!=self.partida.jugadores[0].member.id:
            await interaction.response.send_message("Solo el creador puede cancelar.",ephemeral=True); return
        self.stop(); partidas_truco.pop(self.partida.canal_origen.id,None)
        await interaction.message.edit(content="❌ Sala cancelada.",embed=None,view=None)
        await interaction.response.send_message("Sala cancelada.",ephemeral=True)

class VistaVerCartas(discord.ui.View):
    def __init__(self,partida):
        super().__init__(timeout=600); self.partida=partida

    @discord.ui.button(label="🃏 Ver mis cartas",style=discord.ButtonStyle.primary)
    async def ver_cartas(self,interaction:discord.Interaction,button:discord.ui.Button):
        jugador=next((j for j in self.partida.jugadores if j.member.id==interaction.user.id),None)
        if not jugador:
            await interaction.response.send_message("No estás en esta partida.",ephemeral=True); return
        cartas_txt="\n".join([f"• {carta_str(c)}" for c in jugador.cartas]) or "No tenés cartas."
        embed=discord.Embed(title="🃏 Tus cartas",description=cartas_txt,color=COLOR)
        embed.add_field(name="Tu envido",value=str(calcular_envido(jugador.cartas)),inline=True)
        if self.partida.con_flor and tiene_flor(jugador.cartas):
            embed.add_field(name="🌸 ¡Tenés Flor!",value=str(calcular_flor(jugador.cartas)),inline=True)
        await interaction.response.send_message(embed=embed,ephemeral=True)

class VistaTurno(discord.ui.View):
    def __init__(self,partida,jugador):
        super().__init__(timeout=300); self.partida=partida; self.jugador=jugador

    @discord.ui.button(label="🎯 Ver mis opciones",style=discord.ButtonStyle.primary)
    async def ver_opciones(self,interaction:discord.Interaction,button:discord.ui.Button):
        if interaction.user.id!=self.jugador.member.id:
            await interaction.response.send_message("No es tu turno.",ephemeral=True); return
        if self.partida.esperando_respuesta:
            await interaction.response.send_message("Hay un canto pendiente.",ephemeral=True); return
        if self.partida.jugador_actual().member.id!=self.jugador.member.id:
            await interaction.response.send_message("No es tu turno.",ephemeral=True); return
        cartas_txt="\n".join([f"• {carta_str(c)}" for c in self.jugador.cartas]) or "No tenés cartas."
        embed=discord.Embed(title="🎯 Tu turno",description=f"**Tus cartas:**\n{cartas_txt}",color=COLOR)
        await interaction.response.send_message(embed=embed,view=VistaAcciones(self.partida,self.jugador),ephemeral=True)

class VistaAcciones(discord.ui.View):
    def __init__(self,partida,jugador):
        super().__init__(timeout=300); self.partida=partida; self.jugador=jugador; self._build()

    def _build(self):
        for i,carta in enumerate(self.jugador.cartas):
            btn=discord.ui.Button(label=carta_str(carta),style=discord.ButtonStyle.primary,custom_id=f"carta_{i}",row=0)
            btn.callback=self._carta_callback(i); self.add_item(btn)
        if not self.partida.envido_resuelto and self.partida.ronda_actual==0 and self.partida.estado_envido=="ninguno":
            for tipo,nombre in [("envido","Envido"),("real_envido","Real Envido"),("falta_envido","Falta Envido")]:
                btn=discord.ui.Button(label=nombre,style=discord.ButtonStyle.success,custom_id=tipo,row=1)
                btn.callback=self._canto_envido(tipo,nombre); self.add_item(btn)
            if self.partida.con_flor and tiene_flor(self.jugador.cartas):
                btn=discord.ui.Button(label="🌸 Flor",style=discord.ButtonStyle.success,custom_id="flor",row=1)
                btn.callback=self._canto_envido("flor","Flor"); self.add_item(btn)
        if not self.partida.truco_resuelto:
            estados={"ninguno":("truco","Truco"),"truco":("retruco","Retruco"),"retruco":("vale_cuatro","Vale Cuatro")}
            if self.partida.estado_truco in estados:
                tipo,nombre=estados[self.partida.estado_truco]
                btn=discord.ui.Button(label=nombre,style=discord.ButtonStyle.danger,custom_id=tipo,row=2)
                btn.callback=self._canto_truco(tipo,nombre); self.add_item(btn)
        btn_mazo=discord.ui.Button(label="🏳️ Al mazo",style=discord.ButtonStyle.secondary,custom_id="mazo",row=2)
        btn_mazo.callback=self._al_mazo; self.add_item(btn_mazo)

    def _carta_callback(self,idx):
        async def callback(interaction:discord.Interaction):
            if interaction.user.id!=self.jugador.member.id:
                await interaction.response.send_message("No sos vos.",ephemeral=True); return
            carta=self.jugador.cartas[idx]; self.jugador.cartas.pop(idx)
            self.jugador.cartas_jugadas.append(carta); self.partida.cartas_mesa.append((self.jugador,carta))
            self.stop()
            await self.partida.canal.send(embed=discord.Embed(description=f"🃏 **{self.jugador.member.display_name}** tiró: **{carta_str(carta)}**",color=COLOR))
            await interaction.response.edit_message(content=f"✅ Tiraste **{carta_str(carta)}**.",embed=None,view=None)
            jugadores_ronda=set(j.member.id for j,_ in self.partida.cartas_mesa)
            if len(jugadores_ronda)==len(self.partida.jugadores): await resolver_ronda(self.partida)
            else: self.partida.siguiente_turno(); await mostrar_turno(self.partida)
        return callback

    def _canto_envido(self,tipo,nombre):
        async def callback(interaction:discord.Interaction):
            if interaction.user.id!=self.jugador.member.id:
                await interaction.response.send_message("No sos vos.",ephemeral=True); return
            if self.partida.ronda_actual>0:
                await interaction.response.send_message("El envido solo se canta en la primera ronda.",ephemeral=True); return
            self.partida.estado_envido=tipo; self.partida.envido_cantado_por=self.jugador
            self.partida.esperando_respuesta=True; self.stop()
            embed=discord.Embed(title=f"🎵 ¡{nombre.upper()}!",description=f"**{self.jugador.member.display_name}** cantó **{nombre}**. ¿Quieren?",color=discord.Color.green())
            await self.partida.canal.send(embed=embed,view=VistaRespuestaEnvido(self.partida,self.jugador,tipo))
            await interaction.response.edit_message(content=f"Cantaste **{nombre}**.",embed=None,view=None)
        return callback

    def _canto_truco(self,tipo,nombre):
        async def callback(interaction:discord.Interaction):
            if interaction.user.id!=self.jugador.member.id:
                await interaction.response.send_message("No sos vos.",ephemeral=True); return
            self.partida.estado_truco=tipo; self.partida.truco_cantado_por=self.jugador
            self.partida.esperando_respuesta=True; self.stop()
            embed=discord.Embed(title=f"🎴 ¡{nombre.upper()}!",description=f"**{self.jugador.member.display_name}** cantó **{nombre}**. ¿Quieren?",color=discord.Color.red())
            await self.partida.canal.send(embed=embed,view=VistaRespuestaTruco(self.partida,self.jugador))
            await interaction.response.edit_message(content=f"Cantaste **{nombre}**.",embed=None,view=None)
        return callback

    async def _al_mazo(self,interaction:discord.Interaction):
        if interaction.user.id!=self.jugador.member.id:
            await interaction.response.send_message("No sos vos.",ephemeral=True); return
        eq_ganador=self.partida.get_equipo_contrario(self.jugador)
        pts=max(self.partida.puntos_truco()-1,1); self.partida.puntos[eq_ganador]+=pts; self.stop()
        await self.partida.canal.send(embed=discord.Embed(title="🏳️ Al mazo",description=f"**{self.jugador.member.display_name}** se fue al mazo. Equipo {eq_ganador} suma **{pts}** punto(s).",color=COLOR))
        await interaction.response.edit_message(content="Te fuiste al mazo.",embed=None,view=None)
        await nueva_mano(self.partida)

class VistaRespuestaEnvido(discord.ui.View):
    def __init__(self,partida,cantante,tipo):
        super().__init__(timeout=120); self.partida=partida; self.cantante=cantante; self.tipo=tipo

    def get_jugador(self,user): return next((j for j in self.partida.jugadores if j.member.id==user.id),None)
    def es_rival(self,user):
        j=self.get_jugador(user); return j and not self.partida.es_mismo_equipo(j,self.cantante)

    @discord.ui.button(label="✅ Quiero",style=discord.ButtonStyle.success)
    async def quiero(self,interaction:discord.Interaction,button:discord.ui.Button):
        if not self.es_rival(interaction.user):
            await interaction.response.send_message("Solo el equipo rival puede responder.",ephemeral=True); return
        self.partida.esperando_respuesta=False; self.partida.envido_resuelto=True; self.stop()
        resultados=[]
        for j in self.partida.jugadores:
            if self.partida.con_flor and tiene_flor(j.cartas): resultados.append((j,calcular_flor(j.cartas),"🌸 Flor"))
            else: resultados.append((j,calcular_envido(j.cartas),"Envido"))
        resultados.sort(key=lambda x:x[1],reverse=True)
        ganador_j=resultados[0][0]; eq_ganador=self.partida.get_equipo(ganador_j)
        pts=self.partida.puntos_envido_en_juego(); self.partida.puntos[eq_ganador]+=pts
        desc="\n".join([f"**{j.member.display_name}** ({t}): **{v}** pts" for j,v,t in resultados])
        embed=discord.Embed(title=f"🎵 ¡Gana {ganador_j.member.display_name}!",description=f"{desc}\n\n✅ Equipo {eq_ganador} suma **{pts}** punto(s).",color=COLOR)
        await interaction.response.edit_message(embed=embed,view=None)
        await mostrar_turno(self.partida)

    @discord.ui.button(label="❌ No quiero",style=discord.ButtonStyle.danger)
    async def no_quiero(self,interaction:discord.Interaction,button:discord.ui.Button):
        if not self.es_rival(interaction.user):
            await interaction.response.send_message("Solo el equipo rival puede responder.",ephemeral=True); return
        self.partida.esperando_respuesta=False; self.partida.envido_resuelto=True; self.stop()
        eq_ganador=self.partida.get_equipo(self.cantante); self.partida.puntos[eq_ganador]+=1
        await interaction.response.edit_message(embed=discord.Embed(title="🎵 No querido",description=f"Equipo {eq_ganador} suma **1** punto.",color=COLOR),view=None)
        await mostrar_turno(self.partida)

    @discord.ui.button(label="📈 Falta Envido",style=discord.ButtonStyle.primary)
    async def subir(self,interaction:discord.Interaction,button:discord.ui.Button):
        if not self.es_rival(interaction.user):
            await interaction.response.send_message("Solo el equipo rival puede responder.",ephemeral=True); return
        cantante_nuevo=self.get_jugador(interaction.user)
        self.partida.estado_envido="falta_envido"; self.partida.envido_cantado_por=cantante_nuevo
        embed=discord.Embed(title="🎵 ¡FALTA ENVIDO!",description=f"**{interaction.user.display_name}** subió. ¿Quieren?",color=discord.Color.green())
        await interaction.response.edit_message(embed=embed,view=VistaRespuestaEnvido(self.partida,cantante_nuevo,"falta_envido"))

class VistaRespuestaTruco(discord.ui.View):
    def __init__(self,partida,cantante):
        super().__init__(timeout=120); self.partida=partida; self.cantante=cantante

    def get_jugador(self,user): return next((j for j in self.partida.jugadores if j.member.id==user.id),None)
    def es_rival(self,user):
        j=self.get_jugador(user); return j and not self.partida.es_mismo_equipo(j,self.cantante)

    @discord.ui.button(label="✅ Quiero",style=discord.ButtonStyle.success)
    async def quiero(self,interaction:discord.Interaction,button:discord.ui.Button):
        if not self.es_rival(interaction.user):
            await interaction.response.send_message("Solo el equipo rival puede responder.",ephemeral=True); return
        self.partida.esperando_respuesta=False; self.partida.puntos_truco_en_juego=self.partida.puntos_truco(); self.stop()
        await interaction.response.edit_message(embed=discord.Embed(title="🎴 ¡Aceptado!",description=f"En juego: **{self.partida.puntos_truco_en_juego}** punto(s).",color=COLOR),view=None)
        await mostrar_turno(self.partida)

    @discord.ui.button(label="❌ No quiero",style=discord.ButtonStyle.danger)
    async def no_quiero(self,interaction:discord.Interaction,button:discord.ui.Button):
        if not self.es_rival(interaction.user):
            await interaction.response.send_message("Solo el equipo rival puede responder.",ephemeral=True); return
        self.partida.esperando_respuesta=False; self.partida.truco_resuelto=True; self.stop()
        eq_ganador=self.partida.get_equipo(self.cantante); pts=max(self.partida.puntos_truco()-1,1)
        self.partida.puntos[eq_ganador]+=pts
        await interaction.response.edit_message(embed=discord.Embed(title="🎴 No querido",description=f"Equipo {eq_ganador} suma **{pts}** punto(s).",color=COLOR),view=None)
        await nueva_mano(self.partida)

    @discord.ui.button(label="📈 Retruco",style=discord.ButtonStyle.primary)
    async def retruco(self,interaction:discord.Interaction,button:discord.ui.Button):
        if not self.es_rival(interaction.user):
            await interaction.response.send_message("Solo el equipo rival puede responder.",ephemeral=True); return
        if self.partida.estado_truco in ["retruco","vale_cuatro"]:
            await interaction.response.send_message("No se puede subir más.",ephemeral=True); return
        cantante_nuevo=self.get_jugador(interaction.user)
        self.partida.estado_truco="retruco"; self.partida.truco_cantado_por=cantante_nuevo; self.stop()
        embed=discord.Embed(title="🎴 ¡RETRUCO!",description=f"**{interaction.user.display_name}** cantó Retruco. ¿Quieren?",color=discord.Color.red())
        await interaction.response.edit_message(embed=embed,view=VistaRespuestaTruco(self.partida,cantante_nuevo))

    @discord.ui.button(label="🔝 Vale Cuatro",style=discord.ButtonStyle.danger)
    async def vale_cuatro(self,interaction:discord.Interaction,button:discord.ui.Button):
        if not self.es_rival(interaction.user):
            await interaction.response.send_message("Solo el equipo rival puede responder.",ephemeral=True); return
        if self.partida.estado_truco=="vale_cuatro":
            await interaction.response.send_message("Ya se cantó vale cuatro.",ephemeral=True); return
        cantante_nuevo=self.get_jugador(interaction.user)
        self.partida.estado_truco="vale_cuatro"; self.partida.truco_cantado_por=cantante_nuevo; self.stop()
        embed=discord.Embed(title="🎴 ¡VALE CUATRO!",description=f"**{interaction.user.display_name}** cantó Vale Cuatro. ¿Quieren?",color=discord.Color.red())
        await interaction.response.edit_message(embed=embed,view=VistaRespuestaTruco(self.partida,cantante_nuevo))

# ─── COG ──────────────────────────────────────────────────
class Truco(commands.Cog):
    def __init__(self,bot): self.bot=bot

    @commands.group(name="truco",invoke_without_command=True)
    async def truco(self,ctx):
        embed=discord.Embed(title="🃏 Truco — Ayuda",color=COLOR)
        embed.add_field(name="$truco crear [modo] [puntos] [flor]",value="Ejemplos:\n`$truco crear 1v1 15 sinflor`\n`$truco crear 2v2 30 flor`",inline=False)
        embed.add_field(name="Modos",value="`1v1` — `2v2`",inline=True)
        embed.add_field(name="Puntos",value="`15` — `30`",inline=True)
        embed.add_field(name="Flor",value="`flor` — `sinflor`",inline=True)
        embed.add_field(name="📌 Canal temporal",value="Al iniciar la partida, se crea un canal privado para los jugadores",inline=False)
        await ctx.send(embed=embed)

    @truco.command(name="crear")
    async def crear(self,ctx,modo:str="1v1",puntos:int=15,flor_str:str="sinflor"):
        if ctx.channel.id in partidas_truco:
            await ctx.send(embed=discord.Embed(description="❌ Ya hay una partida en este canal.",color=COLOR_ERROR)); return
        if modo not in ["1v1","2v2"]:
            await ctx.send(embed=discord.Embed(description="❌ Modo inválido.",color=COLOR_ERROR)); return
        if puntos not in [15,30]:
            await ctx.send(embed=discord.Embed(description="❌ Puntos inválidos.",color=COLOR_ERROR)); return
        con_flor=flor_str.lower()=="flor"
        partida=Partida(ctx.channel,modo,puntos,con_flor)
        partidas_truco[ctx.channel.id]=partida
        jugador=Jugador(ctx.author); jugador.equipo=1
        partida.jugadores.append(jugador); partida.equipos[1].append(jugador)
        await ctx.send(embed=crear_embed_sala(partida),view=VistaSala(partida))

    @truco.command(name="terminar")
    @commands.has_permissions(administrator=True)
    async def terminar(self,ctx):
        if ctx.channel.id not in partidas_truco:
            await ctx.send(embed=discord.Embed(description="❌ No hay partida activa.",color=COLOR_ERROR)); return
        partida=partidas_truco.pop(ctx.channel.id)
        await ctx.send(embed=discord.Embed(description="✅ Partida terminada.",color=COLOR))
        if partida.canal and partida.canal!=partida.canal_origen:
            asyncio.create_task(eliminar_canal_temporal(partida.canal,delay=5))

    @crear.error
    async def crear_error(self,ctx,error):
        await ctx.send(embed=discord.Embed(description="❌ Uso: `$truco crear [1v1/2v2] [15/30] [flor/sinflor]`",color=COLOR_ERROR))

async def setup(bot):
    await bot.add_cog(Truco(bot))
