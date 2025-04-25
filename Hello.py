import sys
import site
print("Python version:", sys.version)
print("sys.path:", sys.path)
print("site.getsitepackages():", site.getsitepackages())
import telebot
import random
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telethon.sync import TelegramClient
import config
import asyncio
import logging
import threading
import schedule
import time
import flask

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(config.BOT_TOKEN)

# Инициализация Telethon
client = TelegramClient('session', config.API_ID, config.API_HASH)

# Глобальный событийный цикл для telethon
loop = asyncio.new_event_loop()

# Flask приложение
app = flask.Flask(__name__)
WEBHOOK_URL = f"https://igor-inga.onrender.com/{config.BOT_TOKEN}"

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
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f"Привет, милая Ингуля! Ты мой праздник! 🎉", reply_markup=create_keyboard())

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Ингуля, эта команда пока отдыхает! Попробуй /weather! 🌟", reply_markup=create_keyboard())

# Команда /weather
@bot.message_handler(commands=['weather'])
def send_weather(message):
    try:
        api_key = config.WEATHER_API_KEY
        city = "Dnipro"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        bot.reply_to(message, f"Ингуля, в Днепропетровске {temp}°C, {weather}! ☀️", reply_markup=create_keyboard())
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса погоды: {str(e)}")
        bot.reply_to(message, f"Ой, Ингуля, что-то с погодой не получилось! Давай попробуем позже? 🌦️", reply_markup=create_keyboard())
    except KeyError as e:
        logger.error(f"Ошибка в данных погоды: {str(e)}")
        bot.reply_to(message, f"Ингуля, данные о погоде где-то потерялись! Проверь, пожалуйста, API ключ! 🌦️", reply_markup=create_keyboard())

# Асинхронная функция для отправки новостей
async def get_channel_news_async(chat_id):
    try:
        async with client:
            for channel in channels:
                try:
                    entity = await client.get_entity(channel)
                    messages = await client.get_messages(entity, limit=5)
                    bot.send_message(chat_id, f"📢 Новости из {channel}:")
                    for msg in messages:
                        if msg.message:
                            formatted_message = (
                                "━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🕒 {msg.date.strftime('%d.%m.%Y %H:%M')}\n\n"
                                f"{msg.message}\n"
                                "━━━━━━━━━━━━━━━━━━━━━━"
                            )
                            bot.send_message(chat_id, formatted_message)
                    bot.send_message(chat_id, " ")
                except Exception as e:
                    logger.error(f"Ошибка с каналом {channel}: {str(e)}")
                    bot.send_message(chat_id, f"Ой, Ингуля, новости из {channel} не загрузились. Попробуем позже? 🌟")
    except Exception as e:
        logger.error(f"Ошибка подключения к Telegram: {str(e)}")
        bot.send_message(chat_id, f"Ингуля, что-то пошло не так с подключением к Telegram. Давай попробуем ещё раз? 🌈")

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
def send_daily_message():
    try:
        bot.send_message(config.CHAT_ID, "Ингуля, доброе утро! Ты мой свет, сияй ярче солнца! 🌞💖")
        logger.info("Ежедневное сообщение отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки ежедневного сообщения: {str(e)}")

# Планировщик для ежедневного сообщения
schedule.every().day.at("08:00").do(send_daily_message)

# Функция для запуска планировщика
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

# Обработка текста
@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text.lower()
    chat_id = message.chat.id
    if text == "привет 👋":
        bot.reply_to(message, "Привет-привет, моя звезда! 😊", reply_markup=create_keyboard())
    elif text == "погода ☀️":
        send_weather(message)
    elif text == "новости 📰":
        get_channel_news(chat_id)
        bot.reply_to(message, "Новости отправлены, Ингуля! 📰", reply_markup=create_keyboard())
    elif text == "идеи для праздника 🎈":
        bot.reply_to(message, f"Вот идея, Ингуля: {random.choice(ideas)} 🎉", reply_markup=create_keyboard())
    elif text == "ингуля":
        bot.reply_to(message, "Ой, моя милая Ингуля! Ты как солнышко! 🌞", reply_markup=create_keyboard())
    elif "я тебя люблю" in text:
        bot.reply_to(message, "Ингуля, я тоже тебя люблю! Ты мой свет! 💖", reply_markup=create_keyboard())
    else:
        bot.reply_to(message, f"Ты сказал: {message.text}", reply_markup=create_keyboard())

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
@app.route(f"/{config.BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(flask.request.get_json())
    bot.process_new_updates([update])
    return "OK"

@app.route("/")
def index():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
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

    # Настраиваем webhook
    try:
        logger.info("Запуск бота")
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        app.run(host="0.0.0.0", port=5000)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {str(e)}")
    finally:
        loop.call_soon_threadsafe(loop.stop)
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

if __name__ == "__main__":
    print("Бот запущен, Ингуля! Готов к празднику! 🎉")
    main()
