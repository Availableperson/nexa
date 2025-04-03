import os
import logging
import aiofiles
from aiohttp import web
from aiohttp_middlewares import cors_middleware
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart

# === Настройки ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Токен должен быть в Render Dashboard в переменных окружения
WEB_URL = os.getenv("WEB_URL", "https://example.com")  # Укажи URL фронтенда если нужно
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 10000))

# === Инициализация ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === /start ===
@dp.message(CommandStart())
async def start(message: Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="🚖 Вызвать авто", web_app=WebAppInfo(url=WEB_URL)))
    await message.answer("Добро пожаловать в NexaRide!", reply_markup=keyboard)

# === Главная страница ===
async def handle_home(request):
    return web.Response(text="Сервер работает. Отправьте POST на /ride")

# === Обработка заявки ===
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

# === Загрузка файла ===
async def handle_upload(request):
    reader = await request.multipart()
    field = await reader.next()
    filename = field.filename

    upload_dir = "./uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    async with aiofiles.open(file_path, 'wb') as f:
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            await f.write(chunk)

    logging.info(f"Файл загружен: {file_path}")
    return web.json_response({"status": "ok", "message": f"Файл {filename} получен"})

# === Запуск сервера ===
async def main():
    app = web.Application(middlewares=[cors_middleware(allow_all=True)])
    app.router.add_get("/", handle_home)
    app.router.add_post("/ride", handle_ride)
    app.router.add_post("/upload", handle_upload)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    logging.info(f"Сервер запущен на http://{HOST}:{PORT}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Выход...")
