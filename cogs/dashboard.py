import discord
from discord.ext import commands
from discord import app_commands
import json
import os

PERMISSIONS_FILE = "data/permissions.json"

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ensure_permissions_file()

    def ensure_permissions_file(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(PERMISSIONS_FILE):
            with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump({"roles": {}, "users": {}}, f, indent=4)

    def get_permissions(self):
        with open(PERMISSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_permissions(self, data):
        with open(PERMISSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get_config(self):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)

    def save_config(self, data):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    # ---------------- DASHBOARD PRINCIPAL ----------------
    @app_commands.command(name="hades", description="Ouvre le panneau de contrôle HADES")
    @app_commands.checks.has_permissions(administrator=True)
    async def hades_dashboard(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡️ HADES - Panneau de contrôle",
            description=(
                "Bienvenue dans l'interface d'administration de **HADES**.\n\n"
                "Sélectionne une catégorie ci-dessous pour configurer le bot."
            ),
            color=discord.Color.from_str("#2b2d31")
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="🔐 Vérification", value="Gérer le système de vérification", inline=True)
        embed.add_field(name="🔒 Verrouillage", value="Gérer le code et les salons", inline=True)
        embed.add_field(name="⚙️ Permissions", value="Configurer les permissions par rôle", inline=True)
        embed.set_footer(text="HADES Security System • Interface Admin")

        view = DashboardView(self)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ---------------- CONFIGURATION GÉNÉRALE ----------------
    @app_commands.command(name="config", description="Affiche la configuration actuelle du bot")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_show(self, interaction: discord.Interaction):
        config = self.get_config()
        embed = discord.Embed(
            title="⚙️ Configuration HADES",
            color=discord.Color.blue()
        )
        embed.add_field(name="✅ Rôle vérifié", value=config.get("verified_role", "Non défini"), inline=True)
        embed.add_field(name="🔒 Rôle non vérifié", value=config.get("unverified_role", "Non défini"), inline=True)
        embed.add_field(name="🔑 Code de verrouillage", value=f"`{config.get('lock_code', 'Non défini')}`", inline=False)
        embed.add_field(name="📋 Salon de logs", value=config.get("log_channel", "Non défini"), inline=True)
        embed.set_footer(text="Utilise /setconfig pour modifier")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setconfig", description="Modifie un paramètre du bot")
    @app_commands.describe(parametre="Paramètre à modifier", valeur="Nouvelle valeur")
    @app_commands.choices(parametre=[
        app_commands.Choice(name="Rôle vérifié", value="verified_role"),
        app_commands.Choice(name="Rôle non vérifié", value="unverified_role"),
        app_commands.Choice(name="Code de verrouillage", value="lock_code"),
        app_commands.Choice(name="Salon de logs", value="log_channel"),
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def setconfig(self, interaction: discord.Interaction,
                        parametre: app_commands.Choice[str],
                        valeur: str):
        config = self.get_config()
        config[parametre.value] = valeur
        self.save_config(config)
        await interaction.response.send_message(
            f"✅ `{parametre.name}` mis à jour : `{valeur}`", ephemeral=True
        )

    # ---------------- PERMISSIONS PAR RÔLE ----------------
    @app_commands.command(name="perm_add", description="Autorise un rôle à utiliser une commande")
    @app_commands.describe(role="Rôle à autoriser", commande="Nom de la commande (ex: lock)")
    @app_commands.checks.has_permissions(administrator=True)
    async def perm_add(self, interaction: discord.Interaction, role: discord.Role, commande: str):
        perms = self.get_permissions()
        if str(role.id) not in perms["roles"]:
            perms["roles"][str(role.id)] = []
        if commande not in perms["roles"][str(role.id)]:
            perms["roles"][str(role.id)].append(commande)
            self.save_permissions(perms)
            await interaction.response.send_message(
                f"✅ Le rôle {role.mention} peut désormais utiliser `{commande}`", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ Ce rôle a déjà accès à `{commande}`", ephemeral=True
            )

    @app_commands.command(name="perm_remove", description="Retire l'accès d'un rôle à une commande")
    @app_commands.describe(role="Rôle", commande="Nom de la commande")
    @app_commands.checks.has_permissions(administrator=True)
    async def perm_remove(self, interaction: discord.Interaction, role: discord.Role, commande: str):
        perms = self.get_permissions()
        if str(role.id) in perms["roles"] and commande in perms["roles"][str(role.id)]:
            perms["roles"][str(role.id)].remove(commande)
            self.save_permissions(perms)
            await interaction.response.send_message(
                f"✅ Accès retiré à `{commande}` pour {role.mention}", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ Ce rôle n'avait pas accès à `{commande}`", ephemeral=True
            )

    @app_commands.command(name="perm_list", description="Liste toutes les permissions configurées")
    @app_commands.checks.has_permissions(administrator=True)
    async def perm_list(self, interaction: discord.Interaction):
        perms = self.get_permissions()
        embed = discord.Embed(
            title="🔐 Permissions HADES",
            color=discord.Color.purple()
        )
        if not perms["roles"]:
            embed.description = "*Aucune permission configurée.*"
        else:
            for role_id, cmds in perms["roles"].items():
                role = interaction.guild.get_role(int(role_id))
                role_name = role.mention if role else f"`Rôle supprimé ({role_id})`"
                embed.add_field(
                    name=role_name,
                    value=", ".join(f"`{c}`" for c in cmds) if cmds else "*Aucune*",
                    inline=False
                )
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ---------------- VUES (BOUTONS) ----------------
class DashboardView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=180)
        self.cog = cog

    @discord.ui.button(label="Vérification", emoji="🔐", style=discord.ButtonStyle.primary, custom_id="dash_verif")
    async def verif_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔐 Configuration Vérification",
            description=(
                "**Commandes disponibles :**\n\n"
                "`/setup_verification` - Configurer le message et bouton de vérification\n"
                "`/setconfig` - Changer le rôle vérifié\n\n"
                "**Fonctionnement :**\n"
                "• À l'arrivée, le nouveau membre reçoit le rôle *Non vérifié*\n"
                "• Il clique sur le bouton de vérification\n"
                "• Il reçoit le rôle *Vérifié* et perd le rôle *Non vérifié*"
            ),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Verrouillage", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="dash_lock")
    async def lock_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.cog.get_config()
        embed = discord.Embed(
            title="🔒 Configuration Verrouillage",
            description=(
                f"**Code secret actuel :** `{config.get('lock_code', 'Non défini')}`\n\n"
                "**Commandes disponibles :**\n"
                "`/lock [salon] [code]` - Verrouiller un salon\n"
                "`/unlock [salon] [code]` - Déverrouiller un salon\n"
                "`/lockall [code]` - Verrouiller tous les salons (urgence)\n"
                "`/setcode [nouveau]` - Changer le code secret\n\n"
                "⚠️ Le code est requis pour chaque action !"
            ),
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Permissions", emoji="⚙️", style=discord.ButtonStyle.secondary, custom_id="dash_perms")
    async def perms_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="⚙️ Gestion des Permissions",
            description=(
                "**Commandes disponibles :**\n"
                "`/perm_add [role] [commande]` - Autoriser un rôle\n"
                "`/perm_remove [role] [commande]` - Retirer un accès\n"
                "`/perm_list` - Voir toutes les permissions\n\n"
                "Permet de contrôler précisément qui peut utiliser\n"
                "les commandes de verrouillage par exemple."
            ),
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Paramètres", emoji="📋", style=discord.ButtonStyle.success, custom_id="dash_config")
    async def config_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = self.cog.get_config()
        embed = discord.Embed(
            title="📋 Paramètres actuels",
            color=discord.Color.green()
        )
        embed.add_field(name="✅ Rôle vérifié", value=config.get("verified_role", "❌"), inline=True)
        embed.add_field(name="🔒 Rôle non vérifié", value=config.get("unverified_role", "❌"), inline=True)
        embed.add_field(name="🔑 Code", value=f"`{config.get('lock_code', '❌')}`", inline=True)
        embed.add_field(name="📝 Logs", value=config.get("log_channel", "❌"), inline=True)
        embed.set_footer(text="Modifiable via /setconfig")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Dashboard(bot))
