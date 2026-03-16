import discord
from discord.ext import commands

COLOR       = discord.Color.blurple()
COLOR_ERROR = discord.Color.red()
COLOR_OK    = discord.Color.green()

OWNER_ID = 807469500487696444

# ─── MODAL ────────────────────────────────────────────────
class ModalSugerencia(discord.ui.Modal, title="💡 Enviar Sugerencia"):
    sugerencia = discord.ui.TextInput(
        label="¿Qué querés sugerir?",
        style=discord.TextStyle.long,
        placeholder="Escribí tu sugerencia acá...",
        min_length=10,
        max_length=500,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        user  = interaction.user
        guild = interaction.guild

        emb_dm = discord.Embed(title="💡 Nueva Sugerencia", description=self.sugerencia.value, color=COLOR)
        emb_dm.set_author(name=f"{user.display_name} ({user.name})", icon_url=user.display_avatar.url)
        emb_dm.add_field(name="👤 Usuario", value=f"{user.mention} (`{user.id}`)", inline=True)
        emb_dm.add_field(name="🏠 Servidor", value=guild.name if guild else "DM", inline=True)
        emb_dm.set_footer(text=f"ID: {interaction.id}")

        try:
            owner = await interaction.client.fetch_user(OWNER_ID)
            await owner.send(embed=emb_dm)
        except Exception as e:
            print(f"⚠️ No se pudo mandar DM al owner: {e}")

        await interaction.response.send_message(
            embed=discord.Embed(description="✅ ¡Sugerencia enviada! Gracias por el feedback 🙌", color=COLOR_OK),
            ephemeral=True
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            embed=discord.Embed(description="❌ Ocurrió un error al enviar tu sugerencia.", color=COLOR_ERROR),
            ephemeral=True
        )

# ─── VISTA ────────────────────────────────────────────────
class VistaSugerir(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="💡 Escribir sugerencia", style=discord.ButtonStyle.primary)
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalSugerencia())

# ─── COG ──────────────────────────────────────────────────
class Sugerencias(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.command(name="sugerir", aliases=["sugerencia", "sug"])
    async def sugerir(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass

        emb = discord.Embed(
            title="💡 ¿Tenés alguna sugerencia?",
            description="¿Querés proponer algo nuevo, reportar un problema o dar feedback?\nApretá el botón de abajo para escribirla.",
            color=COLOR
        )
        emb.set_footer(text="Solo vos vas a ver tu sugerencia — es privada")
        await ctx.send(embed=emb, view=VistaSugerir())

async def setup(bot):
    await bot.add_cog(Sugerencias(bot))