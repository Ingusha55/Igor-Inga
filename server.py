from flask import Flask, jsonify, request
from telethon import TelegramClient
from telethon.sessions import StringSession
import requests
import asyncio
import gc
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Отладка
print("!!! Сервер начал запуск !!!")

# Конфигурация
print("Загрузка переменных окружения...")
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
CHAT_ID = os.getenv('CHAT_ID')
SESSION = os.getenv('TELETHON_SESSION', '')

channels = [
    '@konkretnost', '@SergeyNikolaevichBogatyrev', '@moyshasheckel', '@sharanism',
    '@diana_spletni_live', '@SwissVatnik', '@pashatoday_new', '@kotreal',
    '@NSDVDnepre', '@DneprNR', '@rasstrelny', '@dimonundmir',
    '@Pavlova_Maria_live', '@readovkanews', '@KremlinPeresmeshnik',
    '@ukr_2025_ru', '@gruboprostite', '@doposlednego_ukrainca', '@msk_53',
    '@pridnestrovec'
]

# Проверка переменных
print(f"API_ID: {API_ID}")
print(f"API_HASH: {API_HASH}")
print(f"BOT_TOKEN: {BOT_TOKEN}")
print(f"WEATHER_API_KEY: {WEATHER_API_KEY}")
print(f"CHAT_ID: {CHAT_ID}")
print(f"SESSION: {SESSION}")
print(f"Каналы: {channels}")

if not all([API_ID, API_HASH, BOT_TOKEN, WEATHER_API_KEY, CHAT_ID]):
    error_msg = "Не заданы все необходимые переменные окружения: API_ID, API_HASH, BOT_TOKEN, WEATHER_API_KEY, CHAT_ID"
    print(error_msg)
    raise ValueError(error_msg)

# Инициализация клиента
print("Инициализация клиента Telethon...")
try:
    client = TelegramClient(StringSession(SESSION), int(API_ID), API_HASH)
    print("Клиент Telethon успешно создан")
except Exception as e:
    print(f"Ошибка при создании клиента Telethon: {str(e)}")
    raise e

last_news_time = None
news_cache = {}

@app.route('/api/news')
async def get_news():
    print("Запрос на новости...")
    global last_news_time, news_cache
    now = datetime.now()
    if last_news_time and now - last_news_time < timedelta(minutes=5):
        print("Возвращаю кэшированные новости")
        return jsonify({'news': [msg for channel, messages in news_cache.items() for msg in messages]})

    news_cache.clear()
    news = []
    try:
        async with client:
            for channel in channels:
                try:
                    print(f"Загрузка сообщений из {channel}")
                    entity = await client.get_entity(channel)
                    messages = await client.get_messages(entity, limit=5)
                    for msg in messages:
                        if msg.message:
                            formatted = f"🕒 {msg.date.strftime('%d.%m.%Y %H:%M')}\n{msg.message[:1000]}"
                            news.append(formatted)
                            news_cache.setdefault(channel, []).append(formatted)
                    await asyncio.sleep(1)
                except Exception as e:
                    error_msg = f"Ошибка в {channel}: {str(e)}"
                    print(error_msg)
                    news.append(error_msg)
    except Exception as e:
        print(f"Ошибка при загрузке новостей: {str(e)}")
        return jsonify({'news': [f"Ошибка: {str(e)}"]})
    last_news_time = now
    gc.collect()
    print("Новости успешно загружены")
    return jsonify({'news': news})

@app.route('/api/weather')
def get_weather():
    print("Запрос на погоду...")
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather?q=Moscow&appid={WEATHER_API_KEY}&units=metric'
        response = requests.get(url).json()
        weather = f"{response['weather'][0]['description']}, {response['main']['temp']}°C"
        print("Погода загружена")
        return jsonify({'weather': weather})
    except Exception as e:
        print(f"Ошибка при загрузке погоды: {str(e)}")
        return jsonify({'weather': 'Ой, погода не загрузилась!'})

@app.route('/api/alarm', methods=['POST'])
def set_alarm():
    print("Запрос на установку будильника...")
    time = request.json.get('time')
    print(f"Будильник установлен на {time}")
    return jsonify({'message': f'Будильник установлен на {time}'})

if __name__ == '__main__':
    print("Запуск сервера...")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(client.start(bot_token=BOT_TOKEN))
        session_string = client.session.save()
        print(f"Сохрани эту строку сессии в TELETHON_SESSION: {session_string}")
    except Exception as e:
        print(f"Ошибка при старте клиента Telethon: {str(e)}")
        raise e
    app.run(host='0.0.0.0', port=5000)
