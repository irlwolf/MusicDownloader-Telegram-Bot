import os
import asyncio
from aiohttp import web
from run import Bot, BotState # Added BotState to access the client

# 1. Define a tiny health check handler
async def health_check(request):
    return web.Response(text="Bot is alive and healthy!", status=200)

async def main():
    # 2. Setup the Web Server for Koyeb Health Checks
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Get the port from Koyeb environment variables (defaults to 8000)
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    # Start the web server
    print(f"Starting health check server on port {port}...")
    await site.start()

    # 3. Initialize your Telegram Bot
    print("Initializing Telegram Bot...")
    await Bot.initialize()
    
    # 4. Corrected Run Command
    print("Bot is running. Press Ctrl+C to stop.")
    # We use the client inside BotState to keep the loop alive
    await BotState.BOT_CLIENT.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
