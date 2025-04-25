import random
import requests
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telethon.sync import TelegramClient
import asyncio
import logging
import threading
import schedule
import time
import flask
import os
from telegram.error import RetryAfter
import pytz

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Считываем переменные окружения
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
CHAT_ID = os.getenv('CHAT_ID')

# Проверяем, что все переменные окружения заданы
if not all([API_ID, API_HASH, BOT_TOKEN, WEATHER_API_KEY, CHAT_ID]):
    logger.error("Одна или несколько переменных окружения отсутствуют!")
    raise ValueError("Необходимо задать API_ID, API_HASH, BOT_TOKEN, WEATHER_API_KEY и CHAT_ID в переменных окружения")

# Инициализация Telethon
client = TelegramClient('session.session', API_ID, API_HASH)
loop_telethon = asyncio.new_event_loop()
loop_scheduler = asyncio.new_event_loop()

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

# Список каналов
channels = [
    '@konkretnost', '@SergeyNikolaevichBogatyrev', '@moyshasheckel', '@sharanism',
    '@diana_spletni_live', '@SwissVatnik', '@pashatoday_new', '@kotreal',
    '@NSDVDnepre', '@DneprNR', '@rasstrelny', '@dimonundmir',
    '@Pavlova_Maria_live', '@readovkanews', '@KremlinPeresmeshnik',
    '@ostashkonews', '@ukr_2025_ru'
]

# Клавиатура
def create_keyboard():
    keyboard = [
        [KeyboardButton("Привет 👋"), KeyboardButton("Погода ☀️")],
        [KeyboardButton("Новости 📰"), KeyboardButton("Идеи для праздника 🎈")]
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
        logger.info("Отправка запроса на погоду")
        api_key = WEATHER_API_KEY
        city = "Dnipro"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        logger.info("Погода получена, отправляем сообщение")
        update.message.reply_text(f"Ингуля, в Днепропетровске {temp}°C, {weather}! ☀️", reply_markup=create_keyboard())
        logger.info("Сообщение о погоде отправлено")
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса погоды: {str(e)}")
        update.message.reply_text(f"Ой, Ингуля, что-то с погодой не получилось! Давай попробуем позже? 🌦️", reply_markup=create_keyboard())
    except KeyError as e:
        logger.error(f"Ошибка в данных погоды: {str(e)}")
        update.message.reply_text(f"Ингуля, данные о погоде где-то потерялись! Проверь, пожалуйста, API ключ! 🌦️", reply_markup=create_keyboard())
dispatcher.add_handler(CommandHandler("weather", send_weather))

# Асинхронная функция для отправки одной новости из случайного канала
async def get_channel_news_async(chat_id):
    try:
        # Выбираем один случайный канал
        selected_channel = random.choice(channels)
        logger.info(f"Выбран канал: {selected_channel}")
        
        start_time = time.time()
        async with client:
            try:
                logger.info(f"Начало загрузки новости из {selected_channel}")
                channel_start_time = time.time()
                entity = await client.get_entity(selected_channel)
                logger.info("Канал получен")
                messages = await client.get_messages(entity, limit=1)  # Одна последняя новость
                logger.info("Сообщения получены")
                await bot.send_message(chat_id=chat_id, text=f"📢 Последняя новость из {selected_channel}:")
                for msg in messages:
                    if msg.message:  # Загружаем только текст
                        formatted_message = (
                            "━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"🕒 {msg.date.strftime('%d.%m.%Y %H:%M')}\n\n"
                            f"{msg.message}\n"
                            "━━━━━━━━━━━━━━━━━━━━━━"
                        )
                        logger.info("Форматирование сообщения завершено")
                        await bot.send_message(chat_id=chat_id, text=formatted_message)
                        logger.info("Сообщение отправлено")
                logger.info(f"Новость из {selected_channel} загружена за {time.time() - channel_start_time:.2f} сек")
            except Exception as e:
                logger.error(f"Ошибка с каналом {selected_channel}: {str(e)}")
                await bot.send_message(chat_id=chat_id, text=f"Ой, Ингуля, новость из {selected_channel} не загрузилась. Попробуем позже? 🌟")
        logger.info(f"Новость загружена за {time.time() - start_time:.2f} сек")
    except Exception as e:
        logger.error(f"Ошибка подключения к Telegram: {str(e)}")
        await bot.send_message(chat_id=chat_id, text=f"Ингуля, что-то пошло не так с подключением к Telegram. Давай попробуем ещё раз? 🌈")

# Функция для запуска асинхронной задачи в отдельном потоке
def run_async_in_thread(coro):
    future = asyncio.run_coroutine_threadsafe(coro, loop_telethon)
    return future.result()

# Обертка для вызова асинхронной функции
def get_channel_news(chat_id):
    logger.info(f"Запуск загрузки новости для chat_id: {chat_id}")
    try:
        run_async_in_thread(get_channel_news_async(chat_id))
        logger.info("Новость успешно отправлена")
    except Exception as e:
        logger.error(f"Ошибка в get_channel_news: {str(e)}")
        bot.send_message(chat_id, f"Ой, Ингуля, новости не загрузились. Попробуем ещё раз чуть позже? 🌟")

# Асинхронное ежедневное сообщение
async def send_daily_message():
    try:
        logger.info("Отправка ежедневного сообщения")
        await bot.send_message(chat_id=CHAT_ID, text="Ингуля, доброе утро! Ты мой свет, сияй ярче солнца! 🌞💖")
        logger.info("Ежедневное сообщение отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки ежедневного сообщения: {str(e)}")

# Планировщик для ежедневного сообщения
def schedule_with_timezone():
    eest = eslint.timezone('Europe/Kiev')
    schedule.every().day.at("08:00", tz=eest).do(lambda: asyncio.run_coroutine_threadsafe(send_daily_message(), loop_scheduler))
    logger.info("Планировщик настроен на 08:00 EEST")

# Функция для запуска планировщика
def run_scheduler():
    schedule_with_timezone()
    while True:
        schedule.run_pending()
        logger.debug("Планировщик проверяет задачи")
        time.sleep(60)

# Функция для запуска событийного цикла Telethon
def run_loop_telethon():
    asyncio.set_event_loop(loop_telethon)
    loop_telethon.run_forever()

# Функция для запуска событийного цикла планировщика
def run_loop_scheduler():
    asyncio.set_event_loop(loop_scheduler)
    loop_scheduler.run_forever()

# Асинхронный запуск Telethon
async def start_telethon():
    try:
        logger.info("Запуск клиента Telethon")
        await client.connect()
        logger.info("Клиент Telethon запущен")
    except Exception as e:
        logger.error(f"Ошибка запуска Telethon: {str(e)}")
        raise

# Обработка текста
def handle_text(update: Update, context) -> None:
    text = update.message.text.lower()
    chat_id = update.message.chat_id
    logger.info(f"Получено текстовое сообщение: {text}")
    if text == "привет 👋":
        update.message.reply_text("Привет-привет, моя звезда! 😊", reply_markup=create_keyboard())
    elif text == "погода ☀️":
        send_weather(update, context)
    elif text == "новости 📰":
        logger.info("Обработка команды 'Новости 📰'")
        get_channel_news(chat_id)
        update.message.reply_text("Новость отправлена, Ингуля! 📰", reply_markup=create_keyboard())
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

    # Запускаем цикл для планировщика
    scheduler_loop_thread = threading.Thread(target=run_loop_scheduler, daemon=True)
    scheduler_loop_thread.start()

    # Запускаем цикл для Telethon
    telethon_loop_thread = threading.Thread(target=run_loop_telethon, daemon=True)
    telethon_loop_thread.start()

    # Запускаем Telethon
    try:
        run_async_in_thread(start_telethon())
    except Exception as e:
        logger.error(f"Ошибка инициализации Telethon: {str(e)}")
        raise

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
