import random
import requests
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, KeyboardButton
import asyncio
import logging
import threading
import schedule
import time
import flask
import os
from telegram.error import RetryAfter

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Считываем переменные окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
CHAT_ID = os.getenv('CHAT_ID')

# Проверяем, что все переменные окружения заданы
if not all([BOT_TOKEN, WEATHER_API_KEY, CHAT_ID]):
    logger.error("Одна или несколько переменных окружения отсутствуют!")
    raise ValueError("Необходимо задать BOT_TOKEN, WEATHER_API_KEY и CHAT_ID в переменных окружения")

# Flask приложение
app_flask = flask.Flask(__name__)
WEBHOOK_URL = f"https://igor-inga.onrender.com/{BOT_TOKEN}"

# Инициализация бота
updater = Updater(token=BOT_TOKEN, use_context=True)
bot = updater.bot
dispatcher = updater.dispatcher

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

# Клавиатура
def create_keyboard():
    keyboard = [
        [KeyboardButton("Привет 👋"), KeyboardButton("Погода ☀️")],
        [KeyboardButton("Идеи для праздника 🎈")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Команда /start
def send_welcome(update: Update, context) -> None:
    logger.info("Получена команда /start")
    update.message.reply_text(f"Привет, милая Ингуля! Ты мой праздник! 🎉", reply_markup=create_keyboard())
dispatcher.add_handler(CommandHandler("start", send_welcome))

# Команда /help
def send_help(update: Update, context) -> None:
    logger.info("Получена команда /help")
    update.message.reply_text("Ингуля, эта команда пока отдыхает! Попробуй /weather! 🌟", reply_markup=create_keyboard())
dispatcher.add_handler(CommandHandler("help", send_help))

# Команда /weather
def send_weather(update: Update, context) -> None:
    logger.info("Получена команда /weather")
    try:
        api_key = WEATHER_API_KEY
        city = "Dnipro"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        update.message.reply_text(f"Ингуля, в Днепропетровске {temp}°C, {weather}! ☀️", reply_markup=create_keyboard())
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса погоды: {str(e)}")
        update.message.reply_text(f"Ой, Ингуля, что-то с погодой не получилось! Давай попробуем позже? 🌦️", reply_markup=create_keyboard())
    except KeyError as e:
        logger.error(f"Ошибка в данных погоды: {str(e)}")
        update.message.reply_text(f"Ингуля, данные о погоде где-то потерялись! Проверь, пожалуйста, API ключ! 🌦️", reply_markup=create_keyboard())
dispatcher.add_handler(CommandHandler("weather", send_weather))

# Ежедневное сообщение
async def send_daily_message():
    try:
        await bot.send_message(chat_id=CHAT_ID, text="Ингуля, доброе утро! Ты мой свет, сияй ярче солнца! 🌞💖")
        logger.info("Ежедневное сообщение отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки ежедневного сообщения: {str(e)}")

# Планировщик для ежедневного сообщения
loop = asyncio.new_event_loop()
schedule.every().day.at("23:50").do(lambda: asyncio.run_coroutine_threadsafe(send_daily_message(), loop))

# Функция для запуска планировщика
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Функция для запуска событийного цикла в отдельном потоке
def run_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Обработка текста
def handle_text(update: Update, context) -> None:
    text = update.message.text.lower()
    chat_id = update.message.chat_id
    logger.info(f"Получено текстовое сообщение: {text}")
    if text == "привет 👋":
        update.message.reply_text("Привет-привет, моя звезда! 😊", reply_markup=create_keyboard())
    elif text == "погода ☀️":
        send_weather(update, context)
    elif text == "идеи для праздника 🎈":
        update.message.reply_text(f"Вот идея, Ингуля: {random.choice(ideas)} 🎉", reply_markup=create_keyboard())
    elif text == "ингуля":
        update.message.reply_text("Ой, моя милая Ингуля! Ты как солнышко! 🌞", reply_markup=create_keyboard())
    elif "я тебя люблю" in text:
        update.message.reply_text("Ингуля, я тоже тебя люблю! Ты мой свет! 💖", reply_markup=create_keyboard())
    else:
        update.message.reply_text(f"Ты сказал: {text}", reply_markup=create_keyboard())
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

# Webhook маршруты
@app_flask.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    logger.info("Получен запрос на вебхук")
    data = flask.request.get_json()
    logger.info(f"Данные вебхука: {data}")
    update = Update.de_json(data, bot)
    if update:
        logger.info(f"Обновление успешно обработано: {update}")
        updater.dispatcher.process_update(update)
    else:
        logger.error("Не удалось обработать обновление")
    return "OK", 200

@app_flask.route("/")
def index():
    logger.info("Запрос на главная страница")
    return "Bot is running!"

# Инициализация при запуске
def init():
    # Запускаем планировщик
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Запускаем событийный цикл в отдельном потоке
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    # Настраиваем вебхук
    max_retries = 3
    for attempt in range(max_retries):
        try:
            updater.bot.delete_webhook()
            time.sleep(2)
            updater.bot.set_webhook(url=WEBHOOK_URL)
            logger.info(f"Вебхук установлен: {WEBHOOK_URL}")
            break
        except RetryAfter as e:
            logger.warning(f"RetryAfter ошибка: {str(e)}. Ждём {e.retry_after} секунд...")
            time.sleep(e.retry_after)
            if attempt == max_retries - 1:
                logger.error("Не удалось установить вебхук после нескольких попыток")
                raise
        except Exception as e:
            logger.error(f"Ошибка установки вебхука: {str(e)}")
            raise

# Вызываем инициализацию при запуске
init()

if __name__ == "__main__":
    print("Бот запущен, Ингуля! Готов к празднику! 🎉")
