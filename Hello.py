import random
import requests
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telethon.sync import TelegramClient
import config
import asyncio
import logging
import threading
import schedule
import time
import flask
import os

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация Telethon
client = TelegramClient('session', config.API_ID, config.API_HASH)

# Глобальный событийный цикл для telethon
loop = asyncio.new_event_loop()

# Flask приложение
app_flask = flask.Flask(__name__)
WEBHOOK_URL = f"https://igor-inga.onrender.com/{config.BOT_TOKEN}"

# Инициализация бота
application = Application.builder().token(config.BOT_TOKEN).build()
bot = application.bot

# Список идей
ideas = [
    "Шарики и конфетти везде! 🎈",
    "Гирлянды мигают, как твоя улыбка! ✨",
    "Танцы под любимую музыку! 🕺",
    "Уютный вечер с чаем и печеньками ☕",
    "Солнце и молния, как наша эмблема! ⚡️🌞",
    "Караоке с друзьями! 🎤",
    "Пикник с шашлыками! 🍖",
    "Фонарики в саду! 🏮"
]

# Твои каналы
channels = [
    '@konkretnost', '@SergeyNikolaevichBogatyrev', '@moyshasheckel', '@sharanism',
    '@diana_spletni_live', '@SwissVatnik', '@pashatoday_new', '@kotreal',
    '@NSDVDnepre', '@DneprNR', '@rasstrelny', '@dimonundmir',
    '@Pavlova_Maria_live', '@readovkanews', '@KremlinPeresmeshnik',
    '@ostashkonews', '@ukr_2025_ru'
]

# Клавиатура
def create_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Привет 👋"), KeyboardButton("Погода ☀️"))
    keyboard.add(KeyboardButton("Новости 📰"), KeyboardButton("Идеи для праздника 🎈"))
    return keyboard

# Команда /start
async def send_welcome(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f"Привет, милая Ингуля! Ты мой праздник! 🎉", reply_markup=create_keyboard())
application.add_handler(CommandHandler("start", send_welcome))

# Команда /help
async def send_help(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Ингуля, эта команда пока отдыхает! Попробуй /weather! 🌟", reply_markup=create_keyboard())
application.add_handler(CommandHandler("help", send_help))

# Команда /weather
async def send_weather(update: Update, context: CallbackContext) -> None:
    try:
        api_key = config.WEATHER_API_KEY
        city = "Dnipro"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        await update.message.reply_text(f"Ингуля, в Днепропетровске {temp}°C, {weather}! ☀️", reply_markup=create_keyboard())
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса погоды: {str(e)}")
        await update.message.reply_text(f"Ой, Ингуля, что-то с погодой не получилось! Давай попробуем позже? 🌦️", reply_markup=create_keyboard())
    except KeyError as e:
        logger.error(f"Ошибка в данных погоды: {str(e)}")
        await update.message.reply_text(f"Ингуля, данные о погоде где-то потерялись! Проверь, пожалуйста, API ключ! 🌦️", reply_markup=create_keyboard())
application.add_handler(CommandHandler("weather", send_weather))

# Асинхронная функция для отправки новостей
async def get_channel_news_async(chat_id):
    try:
        async with client:
            for channel in channels:
                try:
                    entity = await client.get_entity(channel)
                    messages = await client.get_messages(entity, limit=5)
                    await bot.send_message(chat_id, f"📢 Новости из {channel}:")
                    for msg in messages:
                        if msg.message:
                            formatted_message = (
                                "━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🕒 {msg.date.strftime('%d.%m.%Y %H:%M')}\n\n"
                                f"{msg.message}\n"
                                "━━━━━━━━━━━━━━━━━━━━━━"
                            )
                            await bot.send_message(chat_id, formatted_message)
                    await bot.send_message(chat_id, " ")
                except Exception as e:
                    logger.error(f"Ошибка с каналом {channel}: {str(e)}")
                    await bot.send_message(chat_id, f"Ой, Ингуля, новости из {channel} не загрузились. Попробуем позже? 🌟")
    except Exception as e:
        logger.error(f"Ошибка подключения к Telegram: {str(e)}")
        await bot.send_message(chat_id, f"Ингуля, что-то пошло не так с подключением к Telegram. Давай попробуем ещё раз? 🌈")

# Функция для запуска асинхронной задачи в отдельном потоке
def run_async_in_thread(coro):
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()

# Обертка для вызова асинхронной функции
def get_channel_news(chat_id):
    try:
        run_async_in_thread(get_channel_news_async(chat_id))
    except Exception as e:
        logger.error(f"Ошибка в get_channel_news: {str(e)}")
        bot.send_message(chat_id, f"Ой, Ингуля, новости не загрузились. Попробуем ещё раз чуть позже? 🌟")

# Ежедневное сообщение
async def send_daily_message():
    try:
        await bot.send_message(config.CHAT_ID, "Ингуля, доброе утро! Ты мой свет, сияй ярче солнца! 🌞💖")
        logger.info("Ежедневное сообщение отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки ежедневного сообщения: {str(e)}")

# Планировщик для ежедневного сообщения
schedule.every().day.at("08:00").do(lambda: asyncio.run_coroutine_threadsafe(send_daily_message(), loop))

# Функция для запуска планировщика
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Обработка текста
async def handle_text(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()
    chat_id = update.message.chat_id
    if text == "привет 👋":
        await update.message.reply_text("Привет-привет, моя звезда! 😊", reply_markup=create_keyboard())
    elif text == "погода ☀️":
        await send_weather(update, context)
    elif text == "новости 📰":
        get_channel_news(chat_id)
        await update.message.reply_text("Новости отправлены, Ингуля! 📰", reply_markup=create_keyboard())
    elif text == "идеи для праздника 🎈":
        await update.message.reply_text(f"Вот идея, Ингуля: {random.choice(ideas)} 🎉", reply_markup=create_keyboard())
    elif text == "ингуля":
        await update.message.reply_text("Ой, моя милая Ингуля! Ты как солнышко! 🌞", reply_markup=create_keyboard())
    elif "я тебя люблю" in text:
        await update.message.reply_text("Ингуля, я тоже тебя люблю! Ты мой свет! 💖", reply_markup=create_keyboard())
    else:
        await update.message.reply_text(f"Ты сказал: {update.message.text}", reply_markup=create_keyboard())
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# Функция для запуска событийного цикла в отдельном потоке
def run_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Асинхронный запуск telethon
async def start_telethon():
    try:
        logger.info("Запуск клиента Telethon")
        await client.start()
        logger.info("Клиент Telethon запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска Telethon: {str(e)}")
        raise

# Webhook маршруты
@app_flask.route(f"/{config.BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(flask.request.get_json(), bot)
    application.process_update(update)
    return "OK"

@app_flask.route("/")
def index():
    application.bot.delete_webhook()
    application.bot.set_webhook(url=WEBHOOK_URL)
    return "Bot is running!"

# Основная функция
def main():
    # Запускаем планировщик
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Запускаем событийный цикл в отдельном потоке
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    # Запускаем telethon
    try:
        run_async_in_thread(start_telethon())
    except Exception as e:
        logger.error(f"Ошибка инициализации Telethon: {str(e)}")
        return

    # Настраиваем вебхук и запускаем Flask
    try:
        logger.info("Запуск бота")
        application.bot.delete_webhook()
        application.bot.set_webhook(url=WEBHOOK_URL)
        app_flask.run(host="0.0.0.0", port=5000)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {str(e)}")
    finally:
        loop.call_soon_threadsafe(loop.stop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

if __name__ == "__main__":
    print("Бот запущен, Ингуля! Готов к празднику! 🎉")
    main()
