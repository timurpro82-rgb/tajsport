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

# --- ЗАГРУЗКА КОНФИГУРАЦИИ ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://timurpro82-rgb.github.io/tajsport/index.html")
USERS_DB = "users.json"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

if not API_TOKEN:
    logging.error("❌ BOT_TOKEN не найден в .env файле!")
    sys.exit(1)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ (Простой JSON) ---
def load_users():
    if os.path.exists(USERS_DB):
        with open(USERS_DB, "r") as f:
            try:
                return set(json.load(f))
            except:
                return set()
    return set()

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_DB, "w") as f:
            json.dump(list(users), f)

def escape_html(text):
    return html.escape(str(text))

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    save_user(message.from_user.id)
    web_app = WebAppInfo(url=WEB_APP_URL)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏟️ Открыть Магазин Taj Sport", web_app=web_app)]]
    )
    await message.answer(
        f"Салом, {escape_html(message.from_user.first_name)}! 👋\n\n"
        "Добро пожаловать в оптовый бот <b>TAJSPORT</b>.\n"
        "Нажмите кнопку ниже, чтобы выбрать товары:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ГЛАВНЫЙ ОБРАБОТЧИК ЗАКАЗА (Ловит данные из Mini App)
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def get_web_app_data(message: types.Message):
    raw_data = message.web_app_data.data
    logging.info(f"📦 ПОЛУЧЕНЫ ДАННЫЕ: {raw_data}") 
    
    try:
        data = json.loads(raw_data)
        tg_user = message.from_user
        username = f"@{tg_user.username}" if tg_user.username else "скрыт"

        if data.get('action') == 'order_with_profile':
            items_list = data.get('items', [])
            total = data.get('total', 0)
            items_text = "\n".join([f"🔹 {escape_html(i)}" for i in items_list])

            # Текст для администратора
            admin_text = (
                f"🛍 <b>НОВЫЙ ЗАКАЗ!</b>\n"
                f"━━━━━━━━━━━━━\n"
                f"👤 <b>Клиент:</b> {escape_html(tg_user.first_name)}\n"
                f"🆔 <b>ID:</b> <code>{tg_user.id}</code>\n"
                f"📱 <b>Username:</b> {username}\n"
                f"━━━━━━━━━━━━━\n"
                f"📦 <b>ТОВАРЫ:</b>\n{items_text}\n"
                f"━━━━━━━━━━━━━\n"
                f"💰 <b>ИТОГО: {escape_html(str(total))} TJS</b>"
            )

            # 1. Отправляем уведомление админу
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
            
            # 2. Отвечаем пользователю
            await message.answer(
                "✅ <b>Ваш заказ принят!</b>\n"
                "Наш менеджер свяжется с вами в ближайшее время. 🙏",
                parse_mode="HTML"
            )
            logging.info(f"✅ Заказ успешно отправлен админу {ADMIN_ID}")

    except Exception as e:
        logging.error(f"❌ Ошибка при разборе заказа: {e}")
        await message.answer("⚠️ Произошла ошибка при передаче данных. Попробуйте еще раз.")

# Команда для проверки количества пользователей (только для админа)
@dp.message(Command("users"))
async def count_users(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        users = load_users()
        await message.answer(f"👥 Всего пользователей в базе: {len(users)}")

# --- ЗАПУСК БОТА ---
async def main():
    logging.info("🚀 БОТ TAJSPORT ЗАПУСКАЕТСЯ...")
    logging.info(f"📍 ADMIN_ID установлен: {ADMIN_ID}")
    
    # Удаляем вебхуки, чтобы бот не конфликтовал
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("👋 Бот остановлен.")
