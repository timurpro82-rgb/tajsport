import asyncio
import logging
import json
import sys
import html
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# --- 1. ЗАГРУЗКА НАСТРОЕК ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
# Твой ID: 984166339 (берется из .env или ставится по умолчанию)
ADMIN_ID = int(os.getenv("ADMIN_ID") or 984166339)
WEB_APP_URL = "https://timurpro82-rgb.github.io/tajsport/index.html"

# Настройка логов, чтобы видеть ошибки в терминале
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if not API_TOKEN:
    logging.error("❌ ОШИБКА: BOT_TOKEN не найден в .env!")
    sys.exit(1)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- 2. ОБРАБОТЧИКИ ---

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    # Создаем кнопку внизу экрана (Reply Keyboard)
    # Это КРИТИЧЕСКИ важно для работы tg.sendData()
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏟️ Открыть Магазин TajSport", web_app=WebAppInfo(url=WEB_APP_URL))]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Салом, {html.escape(message.from_user.first_name)}! 👋\n\n"
        "Добро пожаловать в оптовый бот <b>TAJSPORT</b>.\n"
        "Нажмите на кнопку ниже, чтобы выбрать товары:",
        reply_markup=markup,
        parse_mode="HTML"
    )

# Обработка данных из магазина (когда нажали "Оформить заказ")
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def get_web_app_data(message: types.Message):
    raw_json = message.web_app_data.data
    logging.info(f"📦 ПОЛУЧЕН ЗАКАЗ: {raw_json}")
    
    try:
        data = json.loads(raw_json)
        items_list = data.get('items', [])
        total = data.get('total', 0)
        
        # Формируем список товаров
        items_text = "\n".join([f"🔹 {item}" for item in items_list])

        # Текст для АДМИНИСТРАТОРА (тебя)
        admin_report = (
            f"🛍 <b>НОВЫЙ ЗАКАЗ!</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"👤 <b>Клиент:</b> {html.escape(message.from_user.full_name)}\n"
            f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"📱 <b>Username:</b> @{message.from_user.username or 'скрыт'}\n"
            f"━━━━━━━━━━━━━\n"
            f"📦 <b>ТОВАРЫ:</b>\n{items_text}\n"
            f"━━━━━━━━━━━━━\n"
            f"💰 <b>ИТОГО: {total} TJS</b>"
        )

        # 1. Отправляем отчет тебе
        await bot.send_message(ADMIN_ID, admin_report, parse_mode="HTML")
        
        # 2. Отвечаем пользователю
        await message.answer(
            "✅ <b>Ваш заказ успешно отправлен!</b>\n"
            "Наш менеджер свяжется с вами в ближайшее время. 🙏",
            parse_mode="HTML"
        )
        logging.info(f"✅ Уведомление о заказе отправлено админу {ADMIN_ID}")

    except Exception as e:
        logging.error(f"❌ Ошибка обработки заказа: {e}")
        await message.answer("⚠️ Произошла ошибка при оформлении заказа. Попробуйте еще раз.")

# --- 3. ЗАПУСК ---
async def main():
    logging.info("🚀 БОТ TAJSPORT ЗАПУСКАЕТСЯ...")
    logging.info(f"📍 Админ ID: {ADMIN_ID}")
    
    # Удаляем старые сообщения, которые пришли пока бот был выключен
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем чтение сообщений
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Настройка для Windows, чтобы не было ошибок при закрытии
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("👋 Бот остановлен")
