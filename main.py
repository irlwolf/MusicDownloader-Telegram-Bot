import os
import asyncio
from aiohttp import web
# Import BotState to get the actual client object
from run import Bot, BotState 

async def health_check(request):
    return web.Response(text="Bot is online", status=200)

async def main():
    # 1. Start the Health Check server
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health check server active on port {port}")

    # 2. Start the Telegram Client connection first
    print("Connecting to Telegram...")
    await BotState.BOT_CLIENT.start(bot_token=BotState.BOT_TOKEN)

    # 3. Initialize the Bot logic (handlers/database)
    print("Initializing Bot logic...")
    await Bot.initialize()
    
    # 4. Use the correct Telethon run command
    print("Bot is officially running and listening for messages.")
    await BotState.BOT_CLIENT.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
