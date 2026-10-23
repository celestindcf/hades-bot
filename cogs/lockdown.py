import discord
from discord.ext import commands
from discord import app_commands
import json

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    @app_commands.command(name="lock", description="Verrouille un salon avec le code secret")
    @app_commands.describe(
        salon="Salon à verrouiller (vide = salon actuel)",
        code="Code secret de déverrouillage",
        raison="Raison du verrouillage"
    )
    async def lock(self, interaction: discord.Interaction,
                   code: str,
                   salon: discord.TextChannel = None,
                   raison: str = "Aucune raison fournie"):
        
        config = self.get_config()
        if code != config["lock_code"]:
            await interaction.response.send_message(
                "❌ Code secret invalide !", ephemeral=True
            )
            return

        target = salon or interaction.channel
        
        # Sauvegarder les permissions actuelles
        overwrites = target.overwrites_for(interaction.guild.default_role)
        if overwrites.send_messages is False:
            await interaction.response.send_message(
                "⚠️ Ce salon est déjà verrouillé !", ephemeral=True
            )
            return

        # Verrouiller
        await target.set_permissions(
            interaction.guild.default_role,
            send_messages=False,
            reason=f"Lockdown par {interaction.user} | Raison: {raison}"
        )

        embed = discord.Embed(
            title="🔒 Salon verrouillé",
            description=f"Ce salon a été verrouillé par {interaction.user.mention}\n\n**Raison :** {raison}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await target.send(embed=embed)
        await interaction.response.send_message(
            f"✅ Salon {target.mention} verrouillé !", ephemeral=True
        )

        # Log
        log_channel = discord.utils.get(interaction.guild.text_channels, name=config.get("log_channel"))
        if log_channel and log_channel != target:
            log_embed = discord.Embed(
                title="🔒 Verrouillage",
                description=f"**Salon :** {target.mention}\n**Modérateur :** {interaction.user.mention}\n**Raison :** {raison}",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await log_channel.send(embed=log_embed)

    @app_commands.command(name="unlock", description="Déverrouille un salon avec le code secret")
    @app_commands.describe(
        salon="Salon à déverrouiller (vide = salon actuel)",
        code="Code secret"
    )
    async def unlock(self, interaction: discord.Interaction,
                     code: str,
                     salon: discord.TextChannel = None):
        
        config = self.get_config()
        if code != config["lock_code"]:
            await interaction.response.send_message(
                "❌ Code secret invalide !", ephemeral=True
            )
            return

        target = salon or interaction.channel
        await target.set_permissions(
            interaction.guild.default_role,
            send_messages=None,
            reason=f"Déverrouillage par {interaction.user}"
        )

        embed = discord.Embed(
            title="🔓 Salon déverrouillé",
            description=f"Ce salon a été déverrouillé par {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await target.send(embed=embed)
        await interaction.response.send_message(
            f"✅ Salon {target.mention} déverrouillé !", ephemeral=True
        )

    @app_commands.command(name="lockall", description="Verrouille TOUS les salons textuels")
    @app_commands.describe(code="Code secret", raison="Raison")
    @app_commands.checks.has_permissions(administrator=True)
    async def lockall(self, interaction: discord.Interaction, code: str, raison: str = "Urgence"):
        config = self.get_config()
        if code != config["lock_code"]:
            await interaction.response.send_message("❌ Code invalide !", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        count = 0
        for channel in interaction.guild.text_channels:
            try:
                await channel.set_permissions(
                    interaction.guild.default_role,
                    send_messages=False,
                    reason=f"Lockdown total par {interaction.user} | {raison}"
                )
                count += 1
            except discord.Forbidden:
                pass

        await interaction.followup.send(
            f"🔒 **{count}** salons verrouillés !", ephemeral=True
        )

    @app_commands.command(name="setcode", description="Change le code secret de verrouillage")
    @app_commands.describe(nouveau_code="Nouveau code secret")
    @app_commands.checks.has_permissions(administrator=True)
    async def setcode(self, interaction: discord.Interaction, nouveau_code: str):
        config = self.get_config()
        config["lock_code"] = nouveau_code
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        
        await interaction.response.send_message(
            "✅ Code secret mis à jour !", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Lockdown(bot))
