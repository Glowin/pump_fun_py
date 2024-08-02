# In tg_bot.py
import os
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
import asyncio
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.trequest = HTTPXRequest(connection_pool_size=20)
        self.bot = Bot(token=self.bot_token, request=self.trequest)

    async def send_message(self, message):
        try:
            await self.bot.send_message(
                chat_id=self.chat_id, 
                text=message, 
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except TelegramError as e:
            logging.error(f"Failed to send Telegram message: {e}")
            logging.error(f"Message content: {message}")

    def send_message_sync(self, message):
        asyncio.run(self.send_message(message))