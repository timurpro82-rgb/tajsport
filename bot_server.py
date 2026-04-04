import asyncio
import logging
import json
import sys
import html
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

# --- НАСТРОЙКИ ---
API_TOKEN = "8499675270:AAH4Bv-KJMRCn0JHoBRYqG0h3g5JW80JvbI"
ADMIN_ID = 984166339 
WEB_APP_URL = "https://timurpro82-rgb.github.io/tajsport/index.html"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏟️ Магазин TajSport (ОПТ)", web_app=WebAppInfo(url=WEB_APP_URL))]],
        resize_keyboard=True
    )
    await message.answer(f"Салом, {html.escape(message.from_user.first_name)}! 👋\nИспользуйте кнопку ниже:", reply_markup=markup)

@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def handle_order(message: types.Message):
    raw_data = message.web_app_data.data
    try:
        data = json.loads(raw_data)
        client = data.get('client', {})
        c_name = client.get('name', 'Не указано')
        c_phone = client.get('phone', 'Не указано')
        c_city = client.get('city', 'Не указано')
        items = data.get('items', [])
        total = data.get('total', 0)
        items_text = "\n".join([f"🔹 {i}" for i in items])

        report = (
            f"🛍 <b>НОВЫЙ ЗАКАЗ!</b>\n"
            f"👤 ФИО: {html.escape(str(c_name))}\n"
            f"📞 Тел: {html.escape(str(c_phone))}\n"
            f"📍 Город: {html.escape(str(c_city))}\n"
            f"📦 Товары:\n{items_text}\n"
            f"💰 Итого: <b>{total} TJS</b>"
        )
        await bot.send_message(ADMIN_ID, report, parse_mode="HTML")
        await message.answer("✅ Заказ отправлен менеджеру!")
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"⚠️ Ошибка, но данные есть:\n{raw_data}")

async def main():
    print(f"🚀 БОТ ЗАПУЩЕН! Админ: {ADMIN_ID}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
