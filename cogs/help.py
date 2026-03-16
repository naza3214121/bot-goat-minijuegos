import discord
from discord.ext import commands

COLOR = discord.Color.blurple()

JUEGOS = {
    "🃏 Truco":            {"cmd": "$truco crear",          "desc": "Truco argentino 1v1 o 2v2 con envido y flor"},
    "❓ Preguntado":       {"cmd": "$pq crear [n] [segs]",  "desc": "Trivia de 6 categorías. Ej: `$pq crear 10 30`"},
    "🎮 Ahorcado":         {"cmd": "$ah pvp / $ah bot",     "desc": "PvP o vs bot con teclado paginado"},
    "🃏 Chinchón":         {"cmd": "$ch crear [límite]",    "desc": "Baraja española, escaleras y grupos. Ej: `$ch crear 100`"},
    "🟩 Wordle":           {"cmd": "$wordle crear",         "desc": "Adiviná la palabra de 5 letras en 6 intentos"},
    "🔀 Scramble":         {"cmd": "$scramble jugar",       "desc": "Letras mezcladas — el primero en adivinar gana"},
    "🎮 Nunca Nunca":      {"cmd": "$nunca crear [máx]",   "desc": "Cada uno pone su frase, los demás votan"},
    "🪨 Piedra Papel Tijera": {"cmd": "$ppt crear [1/3/5]", "desc": "1v1 al mejor de X rondas"},
    "💡 sugerencias":            {"cmd": "$sugerir o ?sugerir",          "desc": "para sugerir algun juego o para arreglar errores que encuentres"},
}

class VistaHelp(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="🃏 Cartas",      style=discord.ButtonStyle.primary)
    async def cartas(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(title="🃏 Juegos de Cartas", color=discord.Color.gold())
        emb.add_field(name="🃏 Truco",   value="`$truco crear`\nTruco argentino 1v1 o 2v2 con envido, truco y flor.\nCrea canal privado para la partida.", inline=False)
        emb.add_field(name="🃏 Chinchón", value="`$ch crear [límite]`\nBaraja española 2-4 jugadores. Formá escaleras y grupos.\nLímite: 50-200 pts. Crea canal privado.", inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @discord.ui.button(label="🧠 Trivia/Palabras", style=discord.ButtonStyle.primary)
    async def trivia(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(title="🧠 Trivia y Palabras", color=discord.Color.green())
        emb.add_field(name="❓ Preguntado", value="`$pq crear [preguntas] [segundos]`\nTrivia de Historia, Ciencia, Deportes, Geo, Entretenimiento y Tecnología.\nEjemplo: `$pq crear 10 30`", inline=False)
        emb.add_field(name="🎮 Ahorcado",   value="`$ah pvp` — Vos ponés la palabra, otro adivina\n`$ah bot` — El bot elige la palabra\nTeclado visual con paginación A-M / N-Z", inline=False)
        emb.add_field(name="🟩 Wordle",     value="`$wordle crear`\nAdiviná la palabra de 5 letras en 6 intentos.\n🟩 posición correcta · 🟨 en la palabra · ⬛ no está", inline=False)
        emb.add_field(name="🔀 Scramble",   value="`$scramble jugar`\nLetras mezcladas — escribí la palabra en el chat para ganar.\nGlobal, sin sala, 60 segundos.", inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @discord.ui.button(label="🎉 Social", style=discord.ButtonStyle.primary)
    async def social(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(title="🎉 Juegos Sociales", color=discord.Color.purple())
        emb.add_field(name="🎮 Nunca Nunca",  value="`$nunca crear [máx jugadores]`\nCada jugador pone su frase de 'Nunca nunca...' en su turno.\nLos demás votan. El más veterano pierde. Máx: 5-10 jugadores.", inline=False)
        emb.add_field(name="🪨 Piedra Papel Tijera", value="`$ppt crear [1/3/5/7]`\n1v1 al mejor de X rondas. Cada uno elige en secreto.", inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @discord.ui.button(label="⚙️ Admin", style=discord.ButtonStyle.secondary)
    async def admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(title="⚙️ Comandos de Admin", color=discord.Color.red())
        emb.add_field(name="🛑 Terminar partidas", value=(
            "`$truco terminar`\n`$pq terminar`\n`$ah terminar`\n`$ch terminar`\n"
            "`$wordle terminar`\n`$scramble terminar`\n`$trab terminar`\n"
            "`$nunca terminar`\n`$ppt terminar`"
        ), inline=False)
        emb.set_footer(text="Todos los comandos de terminar requieren permisos de Administrador")
        await interaction.response.send_message(embed=emb, ephemeral=True)

class Help(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(name="help", aliases=["ayuda", "h"])
    async def help(self, ctx):
        emb = discord.Embed(
            title="🎮 GOAT Minijuegos — Comandos",
            description="Elegí una categoría para ver los comandos detallados.\nTodos los comandos usan el prefijo **`$`**",
            color=COLOR
        )
        for nombre, info in JUEGOS.items():
            emb.add_field(
                name=f"{nombre}",
                value=f"`{info['cmd']}`\n{info['desc']}",
                inline=True
            )
        emb.set_footer(text="$help | Prefijos: $ o !")
        await ctx.send(embed=emb, view=VistaHelp())

async def setup(bot):
    await bot.add_cog(Help(bot))