import os
import asyncio
from aiohttp import web
from run import Bot
from run.glob_variables import BotState # We need this to access the Client

# 1. This keeps Koyeb happy (Health Check)
async def health_check(request):
    return web.Response(text="Bot is online", status=200)

async def main():
    # 2. Start the Web Server on Port 8000
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health check server active on port {port}")

    # 3. Start the Telegram Client
    print("Connecting to Telegram...")
    # This actually logs the bot in using your token
    await BotState.BOT_CLIENT.start(bot_token=BotState.BOT_TOKEN)

    # 4. Initialize Handlers
    print("Initializing Bot logic...")
    await Bot.initialize()
    
    # 5. The "Keep-Alive" loop
    print("Bot is officially running.")
    # This replaces 'Bot.run()' and keeps the bot listening
    await BotState.BOT_CLIENT.run_until_disconnected()

if __name__ == "__main__":
    try:
        # Use the asyncio from your utils or standard lib
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
