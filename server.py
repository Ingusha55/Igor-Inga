from flask import Flask, jsonify, request
from telethon import TelegramClient
from telethon.sessions import StringSession
import requests
import asyncio
import gc
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Конфигурация из переменных окружения
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
SESSION = os.getenv('TELETHON_SESSION', '')
CHAT_ID = '7208003922'
channels = ['channel1', 'channel2', ...]  # Замени на 17 каналов

# Проверка, что все переменные заданы
if not all([API_ID, API_HASH, BOT_TOKEN, WEATHER_API_KEY]):
    raise ValueError("Не заданы все необходимые переменные окружения: API_ID, API_HASH, BOT_TOKEN, WEATHER_API_KEY")

print(f"Загружена сессия: {SESSION}")  # Отладка

# Инициализация клиента с StringSession
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
    global last_news_time, news_cache
    now = datetime.now()
    if last_news_time and now - last_news_time < timedelta(minutes=5):
        return jsonify({'news': [msg for channel, messages in news_cache.items() for msg in messages]})

    news_cache.clear()
    news = []
    async with client:
        for channel in channels:
            try:
                entity = await client.get_entity(channel)
                messages = await client.get_messages(entity, limit=5)
                for msg in messages:
                    if msg.message:
                        formatted = f"🕒 {msg.date.strftime('%d.%m.%Y %H:%M')}\n{msg.message[:1000]}"
                        news.append(formatted)
                        news_cache.setdefault(channel, []).append(formatted)
                await asyncio.sleep(1)
            except Exception as e:
                news.append(f"Ошибка в {channel}: {str(e)}")
    last_news_time = now
    gc.collect()
    return jsonify({'news': news})

@app.route('/api/weather')
def get_weather():
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather?q=Moscow&appid={WEATHER_API_KEY}&units=metric'
        response = requests.get(url).json()
        weather = f"{response['weather'][0]['description']}, {response['main']['temp']}°C"
        return jsonify({'weather': weather})
    except:
        return jsonify({'weather': 'Ой, погода не загрузилась!'})

@app.route('/api/alarm', methods=['POST'])
def set_alarm():
    time = request.json.get('time')
    return jsonify({'message': f'Будильник установлен на {time}'})

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(client.start(bot_token=BOT_TOKEN))
        session_string = client.session.save()
        print(f"Сохрани эту строку сессии в TELETHON_SESSION: {session_string}")
    except Exception as e:
        print(f"Ошибка при старте клиента Telethon: {str(e)}")
        raise e
    app.run(host='0.0.0.0', port=5000)
