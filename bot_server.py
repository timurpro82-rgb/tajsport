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

# --- ЗАГРУЗКА КОНФИГА ИЗ .env ---
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://timurpro82-rgb.github.io/tajsport/index.html")
USERS_DB = "users.json"

if not API_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле!")
if not ADMIN_ID:
    raise ValueError("❌ ADMIN_ID не найден в .env файле!")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ФУНКЦИИ ДЛЯ БАЗЫ ДАННЫХ ---
def load_users() -> set:
    if os.path.exists(USERS_DB):
        with open(USERS_DB, "r") as f:
            try:
                return set(json.load(f))
            except Exception:
                return set()
    return set()

def save_user(user_id: int):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_DB, "w") as f:
            json.dump(list(users), f)

def escape_html(text) -> str:
    return html.escape(str(text))

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    save_user(message.from_user.id)
    web_app = WebAppInfo(url=WEB_APP_URL)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🏟️ Открыть Магазин Taj Sport", web_app=web_app)
        ]]
    )
    await message.answer(
        f"Салом, {escape_html(message.from_user.first_name)}! 👋\n\n"
        "Добро пожаловать в оптовый бот <b>TAJSPORT</b>.\n"
        "Нажмите кнопку ниже для входа в магазин:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@dp.message(Command("users"))
async def admin_users(message: types.Message):
    """Только для админа — показывает количество пользователей."""
    if message.from_user.id != ADMIN_ID:
        return
    users = load_users()
    await message.answer(f"👥 Всего пользователей: <b>{len(users)}</b>", parse_mode="HTML")

@dp.message(F.web_app_data)
async def get_web_app_data(message: types.Message):
    tg_user = message.from_user
    username = f"@{tg_user.username}" if tg_user.username else "скрыт"
    
    logging.info(f"📦 ПОЛУЧЕН ЗАКАЗ от {tg_user.id}: {message.web_app_data.data}")

    # ОТЛАДКА — покажет что именно пришло от магазина
    logging.info(f"RAW DATA: {message.web_app_data.data}")

    # 1. Парсим JSON
    try:
        data = json.loads(message.web_app_data.data)
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON от {tg_user.id}: {e}")
        await message.answer("❌ Ошибка при обработке заказа. Попробуйте ещё раз.")
        return

    if data.get('action') != 'order_with_profile':
        logging.warning(f"Неизвестный action: {data.get('action')}")
        return

    items_list = data.get('items', [])
    total = data.get('total', 0)

    if not items_list:
        await message.answer("⚠️ Корзина пустая. Добавьте товары и попробуйте снова.")
        return

    items_text = "\n".join([f"🔹 {escape_html(i)}" for i in items_list])

    admin_text = (
        f"🛍 <b>НОВЫЙ ЗАКАЗ!</b>\n"
        f"━━━━━━━━━━━━━\n"
        f"👤 <b>Клиент:</b> {escape_html(tg_user.first_name)}\n"
        f"📱 <b>Username:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{tg_user.id}</code>\n"
        f"━━━━━━━━━━━━━\n"
        f"📦 <b>ТОВАРЫ:</b>\n{items_text}\n"
        f"━━━━━━━━━━━━━\n"
        f"💰 <b>ИТОГО: {escape_html(str(total))} TJS</b>"
    )

    # 2. Отправляем заказ админу (с обработкой ошибок)
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        logging.info(f"Заказ от {tg_user.id} успешно отправлен админу.")
    except Exception as e:
        logging.error(f"Не удалось отправить заказ админу ({ADMIN_ID}): {e}")
        # Сообщаем пользователю, но не пугаем — менеджер всё равно увидит в логах
        await message.answer(
            "⚠️ Ваш заказ получен, но возникла небольшая проблема с уведомлением.\n"
            "Наш менеджер свяжется с вами в ближайшее время.",
            parse_mode="HTML"
        )
        return

    # 3. Подтверждение пользователю
    await message.answer(
        "✅ <b>Ваш заказ принят!</b>\n"
        f"📦 Товаров: {len(items_list)} шт.\n"
        f"💰 Сумма: <b>{escape_html(str(total))} TJS</b>\n\n"
        "Наш менеджер свяжется с вами в ближайшее время. 🙏",
        parse_mode="HTML"
    )

# --- ЗАПУСК ---
async def main():
    print("\n✅ БОТ TAJSPORT ЗАПУЩЕН!")
    print(f"   Admin ID: {ADMIN_ID}")
    print(f"   Web App:  {WEB_APP_URL}\n")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Бот остановлен.")
