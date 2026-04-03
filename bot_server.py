import asyncio
import logging
import json
import sys
import html
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# --- ИНИЦИАЛИЗАЦИЯ ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "984166339"))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://timurpro82-rgb.github.io/tajsport/index.html")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    web_app = WebAppInfo(url=WEB_APP_URL)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏟️ Открыть Магазин", web_app=web_app)]]
    )
    await message.answer(
        f"Салом, {html.escape(message.from_user.first_name)}! 👋\nЗайдите в магазин для заказа:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# 1. Ловушка для ЛЮБЫХ сообщений (поможет понять, что происходит)
@dp.message()
async def all_messages_handler(message: types.Message):
    # Если в сообщении есть данные из WebApp
    if message.web_app_data:
        raw_data = message.web_app_data.data
        logging.info(f"🎯 ВНИМАНИЕ! ДАННЫЕ ПОЛУЧЕНЫ: {raw_data}")
        
        try:
            data = json.loads(raw_data)
            items = "\n".join([f"🔹 {i}" for i in data.get('items', [])])
            total = data.get('total', 0)
            
            admin_text = (
                f"🛍 <b>НОВЫЙ ЗАКАЗ!</b>\n"
                f"👤 Клиент: {message.from_user.first_name}\n"
                f"📦 Товары:\n{items}\n"
                f"💰 Итого: {total} TJS"
            )
            
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
            await message.answer("✅ Заказ отправлен менеджеру!")
            
        except Exception as e:
            logging.error(f"Ошибка парсинга: {e}")
    else:
        # Если это просто текст, а не данные из магазина
        logging.info(f"Обычное сообщение от {message.from_user.id}: {message.text}")

# --- ЗАПУСК ---
async def main():
    logging.info("🚀 БОТ ЗАПУСКАЕТСЯ...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
