import sys
import asyncio
from pathlib import Path
import pyromod # Import pyromod before pyrogram
from pyrogram import Client, __version__, idle
from pyrogram.raw.all import layer
import logging
import logging.config
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script 
from datetime import date, datetime 
import pytz
from aiohttp import web
from plugins import web_server
from util.keepalive import ping_server
from lazybot import LazyPrincessBot
from lazybot.clients import initialize_clients

# Configure logging for Heroku (output to stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)

async def Lazy_start():
    print("--- BOT STARTUP SEQUENCE INITIATED ---")
    
    # 1. Start the Bot Core
    print("Step 1: Starting LazyPrincessBot...")
    try:
        await LazyPrincessBot.start()
        print("✅ SUCCESS: LazyPrincessBot is online!")
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Bot failed to start: {e}")
        return

    # 2. Get Me
    try:
        bot_info = await LazyPrincessBot.get_me()
        LazyPrincessBot.username = bot_info.username
        print(f"✅ SUCCESS: Logged in as @{bot_info.username}")
    except Exception as e:
        print(f"❌ ERROR: Could not get bot info: {e}")

    # 3. Initialize Multi-Clients
    print("Step 2: Initializing Multi-Clients...")
    try:
        await initialize_clients()
        print("✅ SUCCESS: Multi-clients initialized.")
    except Exception as e:
        print(f"⚠️ WARNING: Multi-client initialization failed: {e}")
    
    # 4. Database Setup
    print("Step 3: Connecting to Database & Fetching Banned List...")
    try:
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        print("Step 4: Ensuring Database Indexes...")
        await Media.ensure_indexes()
        print("✅ SUCCESS: Database setup complete.")
    except Exception as e:
        print(f"❌ ERROR: Database setup failed: {e}")

    # 5. Global Temp Variables
    me = await LazyPrincessBot.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    LazyPrincessBot.username = '@' + me.username
    
    logging.info(f"Bot v{__version__} started on {me.username}.")

    # 6. Optional Keep-Alive (Only on Heroku)
    if ON_HEROKU:
        print("Step 5: Starting Keep-Alive Task...")
        asyncio.create_task(ping_server())
    
    # 7. Optional Web Server (Non-blocking)
    if PORT:
        print(f"Step 6: Attempting to start Web Server on port {PORT}...")
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", PORT).start()
            print(f"✅ SUCCESS: Web server live on port {PORT}")
        except Exception as e:
            print(f"⚠️ WARNING: Web server failed: {e}")

    # 8. Startup Notification
    try:
        tz = pytz.timezone('Asia/Kolkata')
        now = datetime.now(tz)
        time_str = now.strftime("%H:%M:%S %p")
        await LazyPrincessBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(date.today(), time_str))
        print("✅ SUCCESS: Startup message sent to LOG_CHANNEL.")
    except Exception as e:
        print(f"⚠️ WARNING: Could not send startup message: {e}")

    print("--- BOT IS NOW FULLY IDLE AND LISTENING ---")
    await idle()


if __name__ == '__main__':
    try:
        asyncio.run(Lazy_start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
