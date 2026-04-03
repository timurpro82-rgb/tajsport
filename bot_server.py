import asyncio
import logging
import json
import sys
import html
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# --- НАСТРОЙКИ ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
# Если в .env ADMIN_ID не подхватится, используем твой ID напрямую
ADMIN_ID = int(os.getenv("ADMIN_ID") or 984166339)
WEB_APP_URL = "https://timurpro82-rgb.github.io/tajsport/index.html"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    # 1. Создаем ОБЫЧНУЮ кнопку (ReplyKeyboard) — через неё sendData работает 100%
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏟️ Открыть Магазин", web_app=WebAppInfo(url=WEB_APP_URL))]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Салом, {html.escape(message.from_user.first_name)}! 👋\n\n"
        "Для оформления заказа используйте кнопку ниже 👇",
        reply_markup=markup
    )

# 2. Ловим ЛЮБЫЕ данные из WebApp
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def get_web_app_data(message: types.Message):
    logging.info(f"🎯 СРАБОТАЛО! Данные: {message.web_app_data.data}")
    
    try:
        data = json.loads(message.web_app_data.data)
        items_list = data.get('items', [])
        total = data.get('total', 0)
        items_text = "\n".join([f"🔹 {i}" for i in items_list])

        admin_text = (
            f"🛍 <b>НОВЫЙ ЗАКАЗ!</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"👤 Клиент: {html.escape(message.from_user.first_name)}\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n"
            f"━━━━━━━━━━━━━\n"
            f"📦 ТОВАРЫ:\n{items_text}\n"
            f"━━━━━━━━━━━━━\n"
            f"💰 ИТОГО: {total} TJS"
        )

        # Отправка админу
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        # Ответ пользователю
        await message.answer("✅ Ваш заказ отправлен! Менеджер свяжется с вами.")
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка при обработке заказа.")

# --- ЗАПУСК ---
async def main():
    logging.info("🚀 БОТ ЗАПУЩЕН")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
