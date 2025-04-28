from flask import Flask, jsonify
import os

app = Flask(__name__)

# Отладка: Проверяем, запускается ли сервер
print("!!! Сервер начал запуск !!!")

# Проверка переменных окружения
print("Загрузка переменных окружения...")
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
SESSION = os.getenv('TELETHON_SESSION', '')

print(f"API_ID: {API_ID}")
print(f"API_HASH: {API_HASH}")
print(f"BOT_TOKEN: {BOT_TOKEN}")
print(f"WEATHER_API_KEY: {WEATHER_API_KEY}")
print(f"SESSION: {SESSION}")

if not all([API_ID, API_HASH, BOT_TOKEN, WEATHER_API_KEY]):
    error_msg = "Не заданы все необходимые переменные окружения: API_ID, API_HASH, BOT_TOKEN, WEATHER_API_KEY"
    print(error_msg)
    raise ValueError(error_msg)

# Минимальный тестовый маршрут
@app.route('/api/test')
def test():
    print("Запрос на /api/test")
    return jsonify({'message': 'Сервер работает!'})

if __name__ == '__main__':
    print("Запуск Flask-сервера...")
    app.run(host='0.0.0.0', port=5000)
