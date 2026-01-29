import os
import asyncio
from aiohttp import web
from run import Bot

# Handler for Koyeb's "ping"
async def health_check(request):
    return web.Response(text="Bot is online", status=200)

async def main():
    # Setup the internal server
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Use the port Koyeb expects (8000)
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Health check server active on port {port}")

    # Start the actual bot
    await Bot.initialize()
    await Bot.run()

if __name__ == "__main__":
    asyncio.run(main())
