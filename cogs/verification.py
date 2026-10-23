import discord
from discord.ext import commands
from discord import app_commands
import json

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending = {}  # user_id -> guild_id

    def get_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    @app_commands.command(name="setup_verification", description="Configure le système de vérification")
    @app_commands.describe(
        salon="Salon où envoyer le message de vérification",
        role_verifie="Rôle donné après vérification"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_verification(self, interaction: discord.Interaction, 
                                  salon: discord.TextChannel, 
                                  role_verifie: discord.Role):
        guild = interaction.guild
        
        # Créer ou récupérer le rôle non vérifié
        unverified_role = discord.utils.get(guild.roles, name="🔒 Non vérifié")
        if not unverified_role:
            try:
                unverified_role = await guild.create_role(
                    name="🔒 Non vérifié",
                    color=discord.Color.dark_gray(),
                    reason="Rôle de vérification HADES"
                )
                # Positionner sous le rôle du bot
                await unverified_role.edit(position=interaction.guild.me.top_role.position - 1)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Je n'ai pas la permission de créer des rôles !", ephemeral=True
                )
                return

        # Mettre à jour la config
        config = self.get_config()
        config["verified_role"] = role_verifie.name
        config["unverified_role"] = unverified_role.name
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        # Créer l'embed de vérification
        embed = discord.Embed(
            title="🛡️ Vérification HADES",
            description=(
                "Bienvenue sur le serveur !\n\n"
                "Pour accéder à l'ensemble du serveur, merci de cliquer sur le bouton ci-dessous.\n\n"
                "**📜 En cliquant, tu acceptes de respecter les règles du serveur.**"
            ),
            color=discord.Color.from_str("#2b2d31")
        )
        embed.set_footer(text="HADES Security System", icon_url=self.bot.user.display_avatar.url)

        view = discord.ui.View(timeout=None)
        button = discord.ui.Button(
            label="✅ Se vérifier",
            style=discord.ButtonStyle.success,
            custom_id="verify_button"
        )
        view.add_item(button)

        await salon.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Système de vérification configuré dans {salon.mention} !",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        if interaction.data.get("custom_id") != "verify_button":
            return

        guild = interaction.guild
        member = interaction.user
        config = self.get_config()

        verified_role = discord.utils.get(guild.roles, name=config["verified_role"])
        unverified_role = discord.utils.get(guild.roles, name=config["unverified_role"])

        if not verified_role:
            await interaction.response.send_message(
                "❌ Le rôle vérifié n'existe plus, contacte un admin.", ephemeral=True
            )
            return

        if verified_role in member.roles:
            await interaction.response.send_message(
                "✅ Tu es déjà vérifié !", ephemeral=True
            )
            return

        try:
            await member.add_roles(verified_role, reason="Vérification HADES")
            if unverified_role and unverified_role in member.roles:
                await member.remove_roles(unverified_role, reason="Vérification HADES")

            embed = discord.Embed(
                title="✅ Vérification réussie",
                description="Tu as maintenant accès à l'ensemble du serveur !",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Log
            log_channel = discord.utils.get(guild.text_channels, name=config.get("log_channel"))
            if log_channel:
                log_embed = discord.Embed(
                    title="🛡️ Nouvelle vérification",
                    description=f"{member.mention} vient de se vérifier.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                log_embed.set_thumbnail(url=member.display_avatar.url)
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Je n'ai pas la permission de modifier tes rôles.", ephemeral=True
            )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Ajoute automatiquement le rôle non vérifié à l'arrivée"""
        config = self.get_config()
        unverified_role = discord.utils.get(member.guild.roles, name=config["unverified_role"])
        if unverified_role:
            try:
                await member.add_roles(unverified_role, reason="Arrivée - Non vérifié")
            except discord.Forbidden:
                pass

async def setup(bot):
    await bot.add_cog(Verification(bot))
