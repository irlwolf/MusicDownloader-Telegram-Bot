import os
import asyncio
from aiohttp import web
from run import Bot, BotState

async def health_check(request):
    return web.Response(text="Bot is alive and healthy!", status=200)

async def main():
    # 1. Setup Web Server
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"Starting health check server on port {port}...")

    # 2. Initialize Bot
    print("Initializing Telegram Bot...")
    await Bot.initialize()
    
    # 3. START the client (This fixes the ConnectionError)
    print("Connecting to Telegram...")
    await BotState.BOT_CLIENT.start(bot_token=BotState.BOT_TOKEN)
    
    # 4. Run until disconnected
    print("Bot is running. Press Ctrl+C to stop.")
    await BotState.BOT_CLIENT.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
