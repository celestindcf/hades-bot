import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

load_dotenv()


def load_config():
    """Charge la config depuis .env / variables d'env (priorité) ou config.json."""
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
            "Définis DISCORD_TOKEN dans les variables d'environnement "
            "ou crée un config.json."
        )

    return config


def validate_token(token: str) -> bool:
    """Valide le format basique d'un token Discord."""
    if not token:
        print("❌ Token vide !")
        return False

    cleaned = token.strip().strip('"').strip("'")

    if cleaned.startswith("Bot "):
        print("❌ Le token ne doit PAS commencer par 'Bot '")
        print("   → Retire le préfixe 'Bot ' dans la variable d'env")
        return False

    if cleaned == "TON_TOKEN_ICI":
        print("❌ Tu utilises le token placeholder de config.example.json !")
        print("   → Mets le VRAI token Discord dans la variable DISCORD_TOKEN")
        return False

    parts = cleaned.split(".")
    if len(parts) != 3:
        print(f"❌ Format de token invalide ({len(parts)} parties, attendu 3)")
        print("   → Un token Discord ressemble à : XXXXXX.YYYYYY.ZZZZZZ")
        return False

    if len(cleaned) < 50:
        print(f"❌ Token trop court ({len(cleaned)} chars) — probablement tronqué")
        return False

    return True


def save_config(config: dict):
    """Sauvegarde dans .env ou config.json."""
    if os.path.exists(".env"):
        lines = []
        mapping = {
            "token": "DISCORD_TOKEN",
            "verified_role": "VERIFIED_ROLE",
            "unverified_role": "UNVERIFIED_ROLE",
            "lock_code": "LOCK_CODE",
            "log_channel": "LOG_CHANNEL",
            "embed_color": "EMBED_COLOR",
        }
        for key, env_key in mapping.items():
            if key in config:
                lines.append(f"{env_key}={config[key]}")
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

# --- DEBUG (masqué pour la sécurité) ---
token = CONFIG["token"]
print(f"🔍 Token détecté : {token[:6]}...{token[-4:]} (longueur: {len(token)})")

if not validate_token(token):
    exit(1)

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


bot = HadesBot()

try:
    print("🚀 Tentative de connexion à Discord...")
    bot.run(CONFIG["token"])
except discord.LoginFailure:
    print("\n" + "=" * 60)
    print("❌ ÉCHEC D'AUTHENTIFICATION")
    print("=" * 60)
    print("Causes possibles :")
    print("  1. Token invalide ou expiré → reset sur le portail Discord")
    print("  2. Token mal copié (espaces, guillemets, 'Bot ')")
    print("  3. Variable DISCORD_TOKEN absente sur Render")
    print("  4. Bot supprimé de l'application Discord")
    print("\n👉 Va sur https://discord.com/developers/applications")
    print("   → Ton app → Bot → Reset Token → Copie le nouveau")
    print("   → Render → Environment → DISCORD_TOKEN = <nouveau>")
    print("=" * 60)
    exit(1)
