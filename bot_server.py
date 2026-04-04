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

# --- 1. НАСТРОЙКИ ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
# Твой ID из .env или напрямую, если .env не подгрузится
ADMIN_ID = int(os.getenv("ADMIN_ID") or 984166339)
WEB_APP_URL = "https://timurpro82-rgb.github.io/tajsport/index.html"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

if not API_TOKEN:
    logging.error("❌ ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- 2. ОБРАБОТЧИКИ ---

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    # Создаем кнопку Reply Keyboard (внизу экрана)
    # Это ОБЯЗАТЕЛЬНО для передачи данных через tg.sendData
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏟️ Магазин TajSport (ОПТ)", web_app=WebAppInfo(url=WEB_APP_URL))]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"Салом, {html.escape(message.from_user.first_name)}! 👋\n\n"
        "Вы вошли в оптовый чат-бот <b>TAJ SPORT</b>.\n"
        "Нажмите на кнопку ниже, пройдите быструю регистрацию и выбирайте товары по оптовым ценам.",
        reply_markup=markup,
        parse_mode="HTML"
    )

# Обработка данных из Mini App (Регистрация + Заказ)
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def get_web_app_data(message: types.Message):
    raw_json = message.web_app_data.data
    logging.info(f"📦 ПОЛУЧЕНЫ ДАННЫЕ: {raw_json}")
    
    try:
        data = json.loads(raw_json)
        
        # Данные клиента из формы регистрации
        client = data.get('client', {})
        name = client.get('name', 'Не указано')
        phone = client.get('phone', 'Не указано')
        city = client.get('city', 'Не указано')
        
        # Данные заказа
        items_list = data.get('items', [])
        total = data.get('total', 0)
        items_text = "\n".join([f"🔹 {item}" for item in items_list])

        # Формируем красивый отчет для АДМИНИСТРАТОРА (тебя)
        admin_report = (
            f"⚡️ <b>НОВЫЙ ОПТОВЫЙ ЗАКАЗ</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"👤 <b>Клиент:</b> {html.escape(name)}\n"
            f"📞 <b>Телефон:</b> <code>{html.escape(phone)}</code>\n"
            f"📍 <b>Город:</b> {html.escape(city)}\n"
            f"━━━━━━━━━━━━━\n"
            f"📦 <b>ТОВАРЫ:</b>\n{items_text}\n"
            f"━━━━━━━━━━━━━\n"
            f"💰 <b>ИТОГО: {total} TJS</b>\n"
            f"👤 <b>Аккаунт:</b> @{message.from_user.username or 'скрыт'}"
        )

        # 1. Отправляем отчет админу
        await bot.send_message(ADMIN_ID, admin_report, parse_mode="HTML")
        
        # 2. Подтверждаем пользователю
        await message.answer(
            "✅ <b>Заказ и данные приняты!</b>\n\n"
            "Наш менеджер проверит наличие товара и свяжется с вами по указанному номеру телефона. Спасибо!",
            parse_mode="HTML"
        )
        logging.info(f"✅ Заказ клиента {name} отправлен админу.")

    except Exception as e:
        logging.error(f"❌ Ошибка парсинга данных: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке данных. Попробуйте еще раз.")

# --- 3. ЗАПУСК БОТА ---
async def main():
    logging.info("🚀 ЗАПУСК БОТА TAJSPORT...")
    
    # Удаляем вебхуки и старые сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запуск опроса серверов Telegram
    await dp.start_polling(bot)

if __name__ == '__main__':
    # Настройка для стабильной работы на Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("👋 Бот остановлен.")