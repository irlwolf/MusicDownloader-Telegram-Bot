import os
import asyncio
from aiohttp import web
from run.bot import Bot
from run.glob_variables import BotState

# 1. Health Check Server for Koyeb
async def health_check(request):
    return web.Response(text="Bot is online and healthy!", status=200)

async def main():
    # 2. Start the Web Server in the background
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Koyeb Health Check active on port {port}")

    # 3. Initialize the Bot Plugins (Database, Spotify, etc.)
    print("Initializing Bot Plugins...")
    await Bot.initialize()
    
    # 4. Start the Client and Event Handlers
    print("Starting Telegram Client...")
    # This calls the @staticmethod async def run() we just updated in bot.py
    await Bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
