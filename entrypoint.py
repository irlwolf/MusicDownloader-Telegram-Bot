import threading
from flask import Flask
import os
from run import Bot # Your existing bot import

# 1. Create a tiny web server
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_web_server():
    # Koyeb provides the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    # 2. Start the web server in a separate thread
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # 3. Start your Telegram Bot
    print("Starting Telegram Bot...")
    Bot().run() # Or whatever your bot's start command is
