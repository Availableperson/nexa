import asyncio
import logging
import os

from aiohttp import web
from aiohttp_middlewares import cors_middleware
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# === Конфигурация ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_URL", "https://nexa-hvic.onrender.com")  # Render domain
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEB_APP_URL}{WEBHOOK_PATH}"  # Например: https://nexa-hvic.onrender.com/webhook

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === /start ===
@dp.message(CommandStart())
async def start(message: Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text="🚖 Вызвать авто", web_app=WebAppInfo(url=WEB_APP_URL)))
    await message.answer("Добро пожаловать в NexaRide!", reply_markup=kb)

# === Ручка для проверки ===
async def handle_home(request):
    return web.Response(text="Сервер работает!")

# === Ручка заказа ===
async def handle_ride(request):
    try:
        data = await request.json()
        dest = data.get("destination")
        lat = data.get("latitude")
        lon = data.get("longitude")

        if not dest or lat is None or lon is None:
            return web.json_response({"status": "error", "message": "Некорректные данные"}, status=400)

        msg = f"🚖 Новая заявка:\n📍 {dest}\n🌍 {lat}, {lon}"
        await bot.send_message(chat_id=5778010807, text=msg)

        return web.json_response({"status": "ok", "message": "✅ Заявка принята"})
    except Exception as e:
        logging.exception("Ошибка в /ride")
        return web.json_response({"status": "error", "message": "Ошибка сервера"}, status=500)

# === Запуск ===
async def main():
    logging.basicConfig(level=logging.INFO)

    await bot.set_webhook(WEBHOOK_URL)

    app = web.Application(middlewares=[cors_middleware(allow_all=True)])
    app.router.add_get("/", handle_home)
    app.router.add_post("/ride", handle_ride)

    # Webhook-путь Telegram
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    await site.start()

    logging.info(f"✅ Webhook слушает {WEBHOOK_URL}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Выход...")
