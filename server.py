from flask import Flask, jsonify, request
from telethon import TelegramClient
import requests
import asyncio
import gc
from datetime import datetime, timedelta

app = Flask(__name__)

# Конфигурация
API_ID = 'YOUR_API_ID'
API_HASH = 'YOUR_API_HASH'
BOT_TOKEN = 'YOUR_BOT_TOKEN'
WEATHER_API_KEY = 'YOUR_WEATHER_API_KEY'
CHAT_ID = '7208003922'
channels = [ '@konkretnost', '@SergeyNikolaevichBogatyrev', '@moyshasheckel', '@sharanism',
    '@diana_spletni_live', '@SwissVatnik', '@pashatoday_new', '@kotreal',
    '@NSDVDnepre', '@DneprNR', '@rasstrelny', '@dimonundmir',
    '@Pavlova_Maria_live',
    '@readovkanews',
    '@KremlinPeresmeshnik',
    '@ukr_2025_ru', '@gruboprostite',
     '@doposlednego_ukrainca', '@msk_53',
      '@pridnestrovec']  # 20 каналов

client = TelegramClient('session', API_ID, API_HASH)
last_news_time = None
news_cache = {}

@app.route('/news')
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

@app.route('/weather')
def get_weather():
    try:
        url = f'http://api.openweathermap.org/data/2.5/weather?q=Moscow&appid={WEATHER_API_KEY}&units=metric'
        response = requests.get(url).json()
        weather = f"{response['weather'][0]['description']}, {response['main']['temp']}°C"
        return jsonify({'weather': weather})
    except:
        return jsonify({'weather': 'Ой, погода не загрузилась!'})

@app.route('/alarm', methods=['POST'])
def set_alarm():
    time = request.json.get('time')
    # Здесь логика будильника (например, сохранить время и отправить уведомление позже)
    return jsonify({'message': f'Будильник установлен на {time}'})

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.start(bot_token=BOT_TOKEN))
    app.run(host='0.0.0.0', port=5000)
