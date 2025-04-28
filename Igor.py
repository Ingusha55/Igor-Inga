import random
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import telebot
import logging
import schedule
import time
import threading
import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Настройка логирования с подробной отладкой
logging.basicConfig(
    level=logging.DEBUG,  # Изменили уровень на DEBUG для большей детализации
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Значения из config.py вставляем прямо сюда
BOT_TOKEN = "7235495752:AAFEY-IvXWteJEEsMnnhM-32pOqGcoW-6Ms"  # Твой токен от @BotFather
WEATHER_API_KEY = "ddcee32da333d6226a276f5087d34bda"  # Твой ключ OpenWeatherMap
CHAT_ID = "7208003922"  # Твой Telegram ID
API_ID = 27907916  # Твой API_ID
API_HASH = "0677e0ea948df23301a0e333a0b43ac2"  # Твой api_hash

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация Telethon
client = TelegramClient('session', API_ID, API_HASH)

# Создаем событийный цикл для Telethon
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

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

# Список каналов (15 каналов, которые ты дала ранее)
channels = [
    '@konkretnost', '@SergeyNikolaevichBogatyrev', '@moyshasheckel', '@sharanism',
    '@diana_spletni_live', '@SwissVatnik', '@pashatoday_new', '@kotreal',
    '@NSDVDnepre', '@DneprNR', '@rasstrelny', '@dimonundmir',
    '@Pavlova_Maria_live',
    '@readovkanews',
    '@KremlinPeresmeshnik',
    '@ukr_2025_ru', '@gruboprostite',
     '@doposlednego_ukrainca', '@msk_53',
      '@pridnestrovec'
]

# Клавиатура с красивыми смайликами
def create_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    logger.debug("Создание клавиатуры")
    keyboard.add(
        KeyboardButton("Привет 👋✨"),
        KeyboardButton("Погода 🌞☁️")
    )
    keyboard.add(
        KeyboardButton("Новости 📰📢"),
        KeyboardButton("Идеи для праздника 🎉🎈")
    )
    logger.debug("Клавиатура создана")
    return keyboard

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    logger.info("Получена команда /start")
    bot.reply_to(
        message,
        "Привет, милая Ингуля! Ты мой праздник! 🎉",
        reply_markup=create_keyboard()
    )
    logger.debug("Сообщение /start отправлено")

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    logger.info("Получена команда /help")
    bot.reply_to(
        message,
        "Ингуля, эта команда пока отдыхает! Попробуй /weather! 🌟",
        reply_markup=create_keyboard()
    )
    logger.debug("Сообщение /help отправлено")

# Команда /weather
@bot.message_handler(commands=['weather'])
def send_weather(message):
    logger.info("Получена команда /weather")
    try:
        api_key = WEATHER_API_KEY
        city = "Dnipro"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        logger.debug(f"Отправка запроса погоды: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"Получены данные погоды: {data}")
        temp = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        bot.reply_to(
            message,
            f"Ингуля, в Днепропетровске {temp}°C, {weather}! ☀️",
            reply_markup=create_keyboard()
        )
        logger.info("Сообщение о погоде отправлено")
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса погоды: {str(e)}")
        bot.reply_to(
            message,
            "Ой, Ингуля, что-то с погодой не так! Попробуй позже! 🌦️",
            reply_markup=create_keyboard()
        )
    except KeyError as e:
        logger.error(f"Ошибка в данных погоды: {str(e)}")
        bot.reply_to(
            message,
            "Ингуля, данные о погоде не пришли! Проверь API ключ! 🌦️",
            reply_markup=create_keyboard()
        )

# Асинхронная функция для получения новостей
async def get_channel_news_async(chat_id):
    logger.debug("Начало получения новостей")
    try:
        async with client:
            logger.debug("Клиент Telethon запущен")
            for channel in channels:
                try:
                    logger.debug(f"Получение сообщений из канала {channel}")
                    entity = await client.get_entity(channel)
                    logger.debug(f"Получена сущность канала {channel}")
                    messages = await client.get_messages(entity, limit=5)
                    logger.debug(f"Получено {len(messages)} сообщений из {channel}")
                    bot.send_message(chat_id, f"📢 Новости из {channel}:")
                    for msg in messages:
                        if msg.message:  # Пропускаем пустые сообщения
                            formatted_message = (
                                "━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"🕒 {msg.date.strftime('%d.%m.%Y %H:%M')}\n\n"
                                f"{msg.message}\n"  # Без ограничения длины
                                "━━━━━━━━━━━━━━━━━━━━━━"
                            )
                            bot.send_message(chat_id, formatted_message)
                            logger.debug(f"Отправлено сообщение из {channel}: {msg.message[:50]}...")
                    bot.send_message(chat_id, " ")
                except Exception as e:
                    logger.error(f"Ошибка с каналом {channel}: {str(e)}")
                    bot.send_message(chat_id, f"Ой, Ингуля, новости из {channel} не загрузились. Попробуем позже? 🌟")
    except Exception as e:
        logger.error(f"Ошибка подключения к Telegram: {str(e)}")
        bot.send_message(chat_id, f"Ингуля, что-то пошло не так с подключением к Telegram. Давай попробуем ещё раз? 🌈")

# Функция для запуска асинхронной задачи в отдельном потоке
def get_channel_news(chat_id):
    logger.debug("Запуск get_channel_news")
    try:
        loop.run_until_complete(get_channel_news_async(chat_id))
        logger.debug("get_channel_news завершён")
    except Exception as e:
        logger.error(f"Ошибка в get_channel_news: {str(e)}")
        bot.send_message(chat_id, f"Ой, Ингуля, новости не загрузились: {str(e)}. Попробуем ещё раз чуть позже? 🌟")

# Ежедневное сообщение (будильник)
def send_daily_message():
    logger.debug("Запуск send_daily_message")
    try:
        bot.send_message(
            CHAT_ID,
            "Ингуля, доброе утро! Ты мой свет, сияй ярче солнца! 🌞💖"
        )
        logger.info("Ежедневное сообщение отправлено")
    except Exception as e:
        logger.error(f"Ошибка отправки ежедневного сообщения: {str(e)}")

# Планировщик для ежедневного сообщения (без pytz, используем локальное время)
def schedule_with_timezone():
    logger.debug("Настройка планировщика")
    schedule.every().day.at("08:00").do(send_daily_message)
    logger.info("Планировщик настроен на 08:00 по локальному времени")

# Функция для запуска планировщика
def run_scheduler():
    schedule_with_timezone()
    while True:
        schedule.run_pending()
        time.sleep(60)
        logger.debug("Планировщик: проверка задач")

# Асинхронная функция для инициализации Telethon
async def init_telethon_async():
    logger.debug("Запуск init_telethon_async")
    try:
        await client.start(
            phone=lambda: input("Ингуля, введи свой номер телефона (с кодом, например +380): "),
            code_callback=lambda: input("Ингуля, введи код, который Telegram прислал: ")
        )
        logger.info("Telethon успешно инициализирован")
    except SessionPasswordNeededError:
        await client.start(
            password=input("Ингуля, введи пароль для двухфакторной аутентификации: ")
        )
        logger.info("Двухфакторная аутентификация пройдена")
    except Exception as e:
        logger.error(f"Ошибка инициализации Telethon: {str(e)}")
        print(f"Ингуля, ошибка при подключении к Telegram: {str(e)}. Проверь API_ID и API_HASH!")
        raise

# Функция для вызова асинхронной инициализации
def init_telethon():
    logger.info("Инициализация Telethon")
    loop.run_until_complete(init_telethon_async())

# Обработка текста
@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text.lower()
    chat_id = message.chat.id
    logger.info(f"Получено текстовое сообщение: {text}")
    if text == "привет 👋✨":
        bot.reply_to(
            message,
            "Привет-привет, моя звезда! 😊",
            reply_markup=create_keyboard()
        )
        logger.debug("Ответ на 'привет' отправлен")
    elif text == "погода 🌞☁️":
        send_weather(message)
    elif text == "новости 📰📢":
        bot.reply_to(message, "Загружаю новости, Ингуля! Подожди немного... 🕒")
        news_thread = threading.Thread(target=get_channel_news, args=(chat_id,))
        news_thread.start()
        news_thread.join()
        bot.reply_to(
            message,
            "Новости отправлены, Ингуля! 📰",
            reply_markup=create_keyboard()
        )
        logger.debug("Новости обработаны")
    elif text == "идеи для праздника 🎉🎈":
        bot.reply_to(
            message,
            f"Вот идея, Ингуля: {random.choice(ideas)} 🎉",
            reply_markup=create_keyboard()
        )
        logger.debug("Идея для праздника отправлена")
    elif text == "ингуля":
        bot.reply_to(
            message,
            "Ой, моя милая Ингуля! Ты как солнышко! 🌞",
            reply_markup=create_keyboard()
        )
        logger.debug("Ответ на 'ингуля' отправлен")
    elif "я тебя люблю" in text:
        bot.reply_to(
            message,
            "Ингуля, я тоже тебя люблю! Ты мой свет! 💖",
            reply_markup=create_keyboard()
        )
        logger.debug("Ответ на 'я тебя люблю' отправлен")
    elif "спасибо" in text:
        bot.reply_to(
            message,
            "Всё для тебя, Ингуля 💞🌹💖",
            reply_markup=create_keyboard()
        )
        logger.debug("Ответ на 'спасибо' отправлен")
    else:
        bot.reply_to(
            message,
            f"Ты сказала: {message.text}",
            reply_markup=create_keyboard()
        )
        logger.debug(f"Ответ на неизвестное сообщение: {message.text}")

# Основная функция
def main():
    # Инициализируем Telethon перед запуском бота
    init_telethon()

    # Запускаем планировщик в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.debug("Планировщик запущен")

    try:
        logger.info("Удаление вебхука перед запуском polling")
        bot.delete_webhook()  # Удаляем вебхук, чтобы использовать polling
        logger.info("Запуск бота")
        bot.polling(non_stop=True, interval=3, timeout=20)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {str(e)}")
    finally:
        loop.run_until_complete(client.disconnect())
        loop.close()
        logger.debug("Событийный цикл закрыт")

if __name__ == "__main__":
    print("Бот запущен, Ингуля! Готов к празднику! 🎉")
    main()
