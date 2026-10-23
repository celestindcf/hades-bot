import discord
from discord.ext import commands
import json
import os

# Chargement de la config
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

intents = discord.Intents.all()

class HadesBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="h!",
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        self.config = config
        self.lock_code = config.get("lock_code", "HADES2025")

    async def setup_hook(self):
        # Chargement des cogs
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Cog chargé : {filename[:-3]}")
        
        # Sync des slash commands
        try:
            synced = await self.tree.sync()
            print(f"🌐 {len(synced)} commandes slash synchronisées")
        except Exception as e:
            print(f"❌ Erreur sync: {e}")

    async def on_ready(self):
        print(f"🔥 HADES est en ligne : {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="la sécurité du serveur 🛡️"
            ),
            status=discord.Status.online
        )

bot = HadesBot()
bot.run(config["token"])
