import telebot
from telebot import types
import requests
import sqlite3
import threading
import time
from datetime import datetime
from bs4 import BeautifulSoup
import json

API_TOKEN = '7801752845:AAFIpBnGziEFHa7k8velKBgrGB8oAZMDYRs'  
bot = telebot.TeleBot(API_TOKEN)
API_KEY = "c44af914d54af66d7e3edfd823d7bc88"  
ADMIN_ID = 1620098891  


conn = sqlite3.connect('weather_forecast.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER PRIMARY KEY
)
''')
conn.commit()


def get_weather(city):
    try:
        res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru")
        data = res.json()
        
        if data.get("cod") != 200:
            return None
        
        weather_info = {
            'temp': data["main"]["temp"],
            'feels_like': data["main"]["feels_like"],
            'description': data["weather"][0]["description"],
            'humidity': data["main"]["humidity"],
            'city': data["name"]
        }
        return weather_info
    except Exception as e:
        print(f"Ошибка получения погоды: {e}")
        return None

def get_eco_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        news_url = "https://ria.ru/ecology/"
        r = requests.get(news_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')

        news_elements = soup.select('a.list-item__title.color-font-hover-only')[:3]
        news_list = []
        
        for item in news_elements:
            title = item.get_text(strip=True)
            link = item.get('href', '')
            if link and title:
                news_list.append(f"📰 {title}\n🔗 {link}")

        return "\n\n".join(news_list) if news_list else "Новости не найдены."
    except Exception as e:
        print(f"Ошибка получения новостей: {e}")
        return "Ошибка при загрузке новостей."


@bot.message_handler(commands=['tp'])
def ask_question(message):
    msg = bot.send_message(message.chat.id, "📝 Напиши свой вопрос, и он будет отправлен администратору.")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    try:
        user = message.from_user
        question = (
            f"📩 Новый вопрос от пользователя:\n\n"
            f"👤 Имя: {user.first_name} {user.last_name or ''}\n"
            f"🔗 Username: @{user.username or '—'}\n"
            f"🆔 ID: {user.id}\n\n"
            f"💬 Вопрос:\n{message.text}"
        )
        bot.send_message(ADMIN_ID, question)
        bot.send_message(message.chat.id, "✅ Вопрос отправлен! Мы скоро свяжемся с вами.")
    except Exception as e:
        print(f"Ошибка отправки вопроса: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при отправке вопроса.")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🌤 Узнать погоду", "📰 Эко-новости")
    markup.add("🌍 Глобальное потепление", "💡 Полезные советы")

    welcome_text = (
        "Привет! Я бот про погоду и климат.\n\n"
        "Выбери действие 👇\n"
        "Или просто напиши название города для прогноза погоды!"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    bot.send_message(message.chat.id, "Что бы задать вопрос пишите /tp")

@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    try:
        cursor.execute('INSERT OR IGNORE INTO subscriptions (user_id) VALUES (?)', (message.chat.id,))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Подписка на ежедневную сводку оформлена!")
    except Exception as e:
        print(f"Ошибка подписки: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при оформлении подписки.")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    try:
        cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (message.chat.id,))
        conn.commit()
        bot.send_message(message.chat.id, "❌ Подписка отменена.")
    except Exception as e:
        print(f"Ошибка отписки: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при отмене подписки.")


@bot.message_handler(content_types=["text"])
def handle_all_messages(message):
    try:
        text = message.text.strip()
        
        # Обработка кнопок
        if text == "🌤 Узнать погоду":
            bot.send_message(message.chat.id, "Напишите название города для получения прогноза погоды")
            return
        
        elif text == "📰 Эко-новости":
            news = get_eco_news()
            bot.send_message(message.chat.id, news)
            return
        
        elif text == "🌍 Глобальное потепление":
            info = (
                "🌍 Глобальное потепление\n\n"
                "Это увеличение средней температуры Земли из-за парниковых газов.\n\n"
                "🌡 Основные причины:\n"
                "• Сжигание топлива\n• Вырубка лесов\n• Индустриализация\n\n"
                "🌿 Как помочь:\n"
                "• Снизьте выбросы\n• Экономьте ресурсы"
            )
            bot.send_message(message.chat.id, info)
            return
        
        elif text == "💡 Полезные советы":
            tips = (
                "💡 Полезные экосоветы:\n\n"
                "1. ⚡ Экономьте электроэнергию\n"
                "2. 🚌 Используйте общественный транспорт\n"
                "3. ♻️ Сортируйте мусор\n"
                "4. 🌱 Откажитесь от одноразового пластика\n"
                "5. 💧 Экономьте воду"
            )
            bot.send_message(message.chat.id, tips)
            return
        
        # Если текст не кнопка и не команда - пробуем получить погоду
        if len(text) < 50 and not text.startswith('/'):
            bot.send_message(message.chat.id, "⏳ Получаю данные о погоде...")
            weather_data = get_weather(text)
            
            if weather_data:
                response = (
                    f"🌤 Погода в {weather_data['city']}:\n"
                    f"🌡 Температура: {round(weather_data['temp'])}°C\n"
                    f"💭 Ощущается как: {round(weather_data['feels_like'])}°C\n"
                    f"☁️ {weather_data['description'].capitalize()}\n"
                    f"💧 Влажность: {weather_data['humidity']}%"
                )
            else:
                response = "❌ Город не найден. Проверьте написание и попробуйте снова."
            
            bot.send_message(message.chat.id, response)
            return
        
        # Если сообщение не распознано
        bot.send_message(message.chat.id, "Выберите действие из меню или напишите название города для прогноза погоды")
    
    except Exception as e:
        print(f"Ошибка обработки сообщения: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке запроса.")

# Ежедневная рассылка
def daily_forecast_job():
    while True:
        try:
            now = datetime.now()
            if now.hour == 8 and now.minute == 0:
                cursor.execute('SELECT user_id FROM subscriptions')
                subscribers = cursor.fetchall()
                
                for (user_id,) in subscribers:
                    try:
                        bot.send_message(user_id, "🌅 Доброе утро! Напишите название города для получения актуального прогноза погоды.")
                    except Exception as e:
                        print(f"Ошибка отправки пользователю {user_id}: {e}")
                
                time.sleep(60)  # Ждем 1 минуту после отправки
            else:
                time.sleep(30)  # Проверяем каждые 30 секунд
        except Exception as e:
            print(f"Ошибка в daily_forecast_job: {e}")
            time.sleep(60)

# Запуск фонового потока
forecast_thread = threading.Thread(target=daily_forecast_job, daemon=True)
forecast_thread.start()

# Обработка ошибок бота
def start_bot():
    while True:
        try:
            print("Бот запущен...")
            bot.polling(none_stop=True, interval=1, timeout=30)
        except Exception as e:
            print(f"Ошибка бота: {e}")
            print("Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()