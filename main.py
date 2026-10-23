import discord
from discord.ext import commands
import json
import os
import asyncio
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()


# ═══════════════════════════════════════════════════════════
#   CONFIGURATION
# ═══════════════════════════════════════════════════════════
def load_config():
    config = {}
    token_from_env = os.getenv("DISCORD_TOKEN")

    if token_from_env:
        config = {
            "token": token_from_env.strip(),
            "verified_role": os.getenv("VERIFIED_ROLE", "✅ Vérifié"),
            "unverified_role": os.getenv("UNVERIFIED_ROLE", "🔒 Non vérifié"),
            "lock_code": os.getenv("LOCK_CODE", "HADES2025"),
            "log_channel": os.getenv("LOG_CHANNEL", "logs-hades"),
            "embed_color": os.getenv("EMBED_COLOR", "2b2d31"),
        }
        print("✅ Config chargée depuis les variables d'environnement")
    elif os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        print("✅ Config chargée depuis config.json")
    else:
        raise FileNotFoundError(
            "❌ Aucune configuration trouvée !\n"
            "Définis DISCORD_TOKEN dans les variables d'environnement."
        )
    return config


def validate_token(token: str) -> bool:
    if not token:
        print("❌ Token vide !")
        return False
    cleaned = token.strip().strip('"').strip("'")
    if cleaned.startswith("Bot "):
        print("❌ Le token ne doit PAS commencer par 'Bot '")
        return False
    if cleaned == "TON_TOKEN_ICI":
        print("❌ Token placeholder détecté !")
        return False
    if len(cleaned.split(".")) != 3:
        print("❌ Format de token invalide (attendu 3 parties)")
        return False
    if len(cleaned) < 50:
        print(f"❌ Token trop court ({len(cleaned)} chars)")
        return False
    return True


def save_config(config: dict):
    if os.path.exists(".env"):
        mapping = {
            "token": "DISCORD_TOKEN",
            "verified_role": "VERIFIED_ROLE",
            "unverified_role": "UNVERIFIED_ROLE",
            "lock_code": "LOCK_CODE",
            "log_channel": "LOG_CHANNEL",
            "embed_color": "EMBED_COLOR",
        }
        lines = [f"{env_key}={config[key]}" for key, env_key in mapping.items() if key in config]
        with open(".env", "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    else:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)


try:
    CONFIG = load_config()
except FileNotFoundError as e:
    print(e)
    exit(1)

token = CONFIG["token"]
print(f"🔍 Token détecté : {token[:6]}...{token[-4:]} (longueur: {len(token)})")

if not validate_token(token):
    exit(1)


# ═══════════════════════════════════════════════════════════
#   BOT DISCORD
# ═══════════════════════════════════════════════════════════
intents = discord.Intents.all()


class HadesBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="h!",
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        self.config = CONFIG
        self.lock_code = CONFIG.get("lock_code", "HADES2025")

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "__init__.py":
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"✅ Cog chargé : {filename[:-3]}")

        try:
            synced = await self.tree.sync()
            print(f"🌐 {len(synced)} commandes slash synchronisées")
        except Exception as e:
            print(f"❌ Erreur sync: {e}")

    async def on_ready(self):
        print(f"🔥 HADES en ligne : {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="la sécurité du serveur 🛡️"
            ),
            status=discord.Status.online
        )


# ═══════════════════════════════════════════════════════════
#   SERVEUR HTTP (pour Fly.io / Render health checks)
# ═══════════════════════════════════════════════════════════
async def health_check(request):
    """Endpoint de health check pour Fly.io."""
    return web.Response(
        text=json.dumps({
            "status": "ok",
            "bot": "HADES",
            "ready": bot.is_ready() if 'bot' in globals() else False
        }),
        content_type="application/json"
    )


async def root(request):
    """Page racine simple."""
    return web.Response(
        text="🛡️ HADES Security Bot is running",
        content_type="text/plain"
    )


async def start_web_server():
    """Démarre un serveur HTTP minimal pour les health checks Fly.io."""
    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_get("/health", health_check)
    app.router.add_get("/healthz", health_check)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Serveur HTTP démarré sur 0.0.0.0:{port}")


# ═══════════════════════════════════════════════════════════
#   LANCEMENT
# ═══════════════════════════════════════════════════════════
bot = HadesBot()


async def main():
    # Démarre le serveur HTTP AVANT le bot (pour que Fly.io détecte le port)
    await start_web_server()
    print("🚀 Tentative de connexion à Discord...")

    try:
        await bot.start(CONFIG["token"])
    except discord.LoginFailure:
        print("\n" + "=" * 60)
        print("❌ ÉCHEC D'AUTHENTIFICATION")
        print("=" * 60)
        print("  1. Token invalide ou expiré → reset sur le portail Discord")
        print("  2. Token mal copié (espaces, guillemets, 'Bot ')")
        print("  3. Variable DISCORD_TOKEN absente")
        print("=" * 60)
        exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Arrêt du bot...")
