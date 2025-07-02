import asyncio
import os
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def test_bot():
    try:
        print(f"🔍 Test de connexion avec le token: {TOKEN[:10]}...")
        
        bot = Bot(token=TOKEN)
        
        # Test de récupération des infos du bot
        me = await bot.get_me()
        print(f"✅ Bot connecté: {me.first_name} (@{me.username})")
        
        # Test de récupération des updates
        updates = await bot.get_updates()
        print(f"📨 Updates disponibles: {len(updates)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot()) 