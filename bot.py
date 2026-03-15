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
    print('Initalizing The Movie Provider Bot...')
    try:
        await LazyPrincessBot.start()
        logging.info("Bot started successfully!")
    except Exception as e:
        logging.critical(f"Bot failed to start: {e}")
        return

    bot_info = await LazyPrincessBot.get_me()
    LazyPrincessBot.username = bot_info.username
    
    print("Initializing Multi-Clients...")
    await initialize_clients()
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
        
    try:
        print("Ensuring Database Indexes...")
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await Media.ensure_indexes()
    except Exception as e:
        logging.warning(f"Database initialization error: {e}")
    
    me = await LazyPrincessBot.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    LazyPrincessBot.username = '@' + me.username
    
    logging.info(f"{me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
    
    # Optional Web Server for Streaming (Won't block startup in worker mode)
    if PORT:
        print(f"Starting optional Web Server on port {PORT}...")
        try:
            app = web.AppRunner(await web_server())
            await app.setup()
            await web.TCPSite(app, "0.0.0.0", PORT).start()
            logging.info(f"Web server started on port {PORT}")
        except Exception as e:
            logging.error(f"Could not start web server: {e}")

    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    
    try:
        await LazyPrincessBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    except Exception as e:
        logging.warning(f"Could not send startup message to LOG_CHANNEL: {e}")
        
    await idle()


if __name__ == '__main__':
    try:
        asyncio.run(Lazy_start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
