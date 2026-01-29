import os
import asyncio
from aiohttp import web
# Try to import from the specific files if 'from run' fails
from run.bot import Bot
from run.glob_variables import BotState

async def health_check(request):
    return web.Response(text="Bot is online", status=200)

async def main():
    # 1. Health Check Server
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

    # 2. Start Connection
    print("Connecting to Telegram...")
    await BotState.BOT_CLIENT.start(bot_token=BotState.BOT_TOKEN)

    # 3. Initialize Logic
    print("Initializing Bot logic...")
    await Bot.initialize()
    
    # 4. Keep Alive
    print("Bot is officially running.")
    await BotState.BOT_CLIENT.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
