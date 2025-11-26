import os
import telebot
from telebot import types
import json
import datetime
import time
from flask import Flask, request

# Конфигурация
TOKEN = os.environ.get('BOT_TOKEN', '8533622514:AAG-3A6UYXibeRyp6-HCh2pkFb4Tt_OWAjA')
SARA_CHAT_ID = os.environ.get('SARA_CHAT_ID', '1924079795')
SARA_USERNAME = os.environ.get('SARA_USERNAME', '@swinsara')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_states = {}

# Вебхук маршруты
@app.route('/')
def index():
    return "💝 Бот комплиментов для Сары работает! ✨"

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'OK'

# Функции бота
@bot.message_handler(commands=['start'])
def start_command(message):
    user_name = message.from_user.first_name

    welcome_text = f"""
👋 Привет, {user_name}!

Я бот для отправки комплиментов Саре! 💝

📊 Статистика:
• Всего отправлено комплиментов: {get_compliments_count()}
• Последний комплимент: {get_last_compliment_time()}

Нажми "💐 Сделать комплимент" чтобы порадовать Сару! ✨
    """

    show_main_menu(message.chat.id, welcome_text)

def show_main_menu(chat_id, text=None):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton('💐 Сделать комплимент')
    btn2 = types.KeyboardButton('📊 Статистика')
    btn3 = types.KeyboardButton('ℹ️ О боте')
    markup.add(btn1, btn2, btn3)

    if text:
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.send_message(chat_id, "🏠 Главное меню:", reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats_command(message):
    stats_text = f"""
📊 Статистика комплиментов:

Всего комплиментов: {get_compliments_count()}
Последний комплимент: {get_last_compliment_time()}

💝 Сара получает все комплименты мгновенно!
    """
    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(commands=['myid'])
def get_my_id(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    first_name = message.from_user.first_name

    bot.reply_to(message, 
                f"👤 Твои данные:\n"
                f"Имя: {first_name}\n"
                f"User ID: {user_id}\n"
                f"Chat ID: {chat_id}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text

    if text == '💐 Сделать комплимент':
        ask_anonymity(message)
    elif text == '📊 Статистика':
        stats_command(message)
    elif text == 'ℹ️ О боте':
        about_command(message)
    elif user_id in user_states:
        state = user_states[user_id]['state']
        if state == 'choosing_anonymity':
            handle_anonymity_choice(message)
        elif state == 'waiting_for_compliment':
            process_compliment(message)
    else:
        show_main_menu(message.chat.id, "Используйте меню для навигации:")

def about_command(message):
    about_text = f"""
ℹ️ О боте:

Этот бот собирает и отправляет комплиментов для {SARA_USERNAME}!

✨ Как работает:
1. Вы выбираете - анонимно или с именем
2. Пишете комплимент
3. Сара получает комплимент мгновенно!

💝 Дарите добро - это прекрасно!
    """
    bot.send_message(message.chat.id, about_text)

def ask_anonymity(message):
    user_id = message.from_user.id
    user_states[user_id] = {
        'state': 'choosing_anonymity',
        'user_name': message.from_user.first_name,
        'username': f"@{message.from_user.username}" if message.from_user.username else None
    }

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('👤 От своего имени')
    btn2 = types.KeyboardButton('🎭 Анонимно')
    btn3 = types.KeyboardButton('❌ Отмена')
    markup.add(btn1, btn2, btn3)

    instruction_text = """
✍️ Как отправить комплимент?

Выберите вариант отправки:

👤 От своего имени - Сара увидит ваше имя
🎭 Анонимно - Сара не узнает, кто отправил

Выбирайте! 💫
    """

    bot.send_message(message.chat.id, instruction_text, reply_markup=markup)

def handle_anonymity_choice(message):
    user_id = message.from_user.id
    text = message.text

    if text == '❌ Отмена':
        user_states.pop(user_id, None)
        show_main_menu(message.chat.id, "❌ Отправка комплимента отменена.")
        return

    if text == '👤 От своего имени':
        user_states[user_id]['anonymous'] = False
        user_states[user_id]['state'] = 'waiting_for_compliment'
        ask_for_compliment(message, anonymous=False)

    elif text == '🎭 Анонимно':
        user_states[user_id]['anonymous'] = True
        user_states[user_id]['state'] = 'waiting_for_compliment'
        ask_for_compliment(message, anonymous=True)

    else:
        bot.send_message(message.chat.id, "❌ Пожалуйста, выберите вариант из меню")

def ask_for_compliment(message, anonymous=False):
    user_id = message.from_user.id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_btn = types.KeyboardButton('❌ Отмена')
    markup.add(cancel_btn)

    if anonymous:
        instruction_text = """
🎭 Анонимная отправка

Напишите ваш комплимент для Сары:

Сара получит сообщение без указания вашего имени.

💡 Примеры:
• Ты очень добрая и умная!
• У тебя прекрасное чувство юмора!
• Просто что-нибудь хорошее 🐸

Будьте искренни! ✨
        """
    else:
        user_name = user_states[user_id]['user_name']
        instruction_text = f"""
👤 Отправка от вашего имени

Напишите ваш комплимент для Сары:

Сара увидит, что комплимент от {user_name}

💡 Примеры:
• Сара, ты очень добрая и умная!
• Мне нравится твоя энергетика!
• Хочу сказать тебе что-то приятное 🐸

Будьте искренни! ✨
        """

    bot.send_message(message.chat.id, instruction_text, reply_markup=markup)

def process_compliment(message):
    user_id = message.from_user.id
    compliment_text = message.text

    if compliment_text == '❌ Отмена':
        user_states.pop(user_id, None)
        show_main_menu(message.chat.id, "❌ Отправка комплимента отменена.")
        return

    if len(compliment_text) < 3:
        bot.send_message(message.chat.id, "❌ Комплимент слишком короткий!")
        return

    if len(compliment_text) > 1000:
        bot.send_message(message.chat.id, "❌ Комплимент слишком длинный!")
        return

    try:
        user_data = user_states[user_id]
        is_anonymous = user_data['anonymous']

        if is_anonymous:
            display_name = "Аноним 🎭"
            username = "Аноним"
        else:
            display_name = user_data['user_name']
            username = user_data['username'] or "Пользователь"

        save_compliment_to_file(display_name, username, compliment_text, is_anonymous)

        send_success = send_compliment_to_sara(display_name, username, compliment_text, is_anonymous)

        user_states.pop(user_id, None)

        success_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        new_compliment_btn = types.KeyboardButton('💐 Сделать комплимент')
        menu_btn = types.KeyboardButton('🏠 Главное меню')
        success_markup.add(new_compliment_btn, menu_btn)

        if send_success:
            if is_anonymous:
                anonymity_text = "🎭 Ваш комплимент отправлен анонимно"
            else:
                anonymity_text = f"👤 Ваш комплимент отправлен от имени {display_name}"

            success_text = f"""
✅ Комплимент отправлен! 

{anonymity_text}

💝 Сара уже получила ваш комплимент!

📊 Всего комплиментов: {get_compliments_count()}

Хотите отправить еще один? ✨
            """
        else:
            success_text = f"""
✅ Комплимент сохранен! 

💝 Комплимент записан в базу данных!

📊 Всего комплиментов: {get_compliments_count()}

Спасибо за доброе слово! 💐
            """

        bot.send_message(message.chat.id, success_text, reply_markup=success_markup)

    except Exception as e:
        error_text = f"❌ Ошибка: {str(e)}"
        bot.send_message(message.chat.id, error_text)
        user_states.pop(user_id, None)
        show_main_menu(message.chat.id)

def save_compliment_to_file(user_name, username, compliment_text, is_anonymous):
    try:
        compliment_data = {
            'user_name': user_name,
            'username': username,
            'compliment': compliment_text,
            'anonymous': is_anonymous,
            'timestamp': datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        }

        try:
            with open('compliments.json', 'r', encoding='utf-8') as f:
                compliments = json.load(f)
        except FileNotFoundError:
            compliments = []

        compliments.append(compliment_data)

        with open('compliments.json', 'w', encoding='utf-8') as f:
            json.dump(compliments, f, ensure_ascii=False, indent=2)

        anonymity = "анонимно" if is_anonymous else "от имени"
        print(f"💌 Новый комплимент {anonymity} {user_name}: {compliment_text}")

    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
        raise e

def send_compliment_to_sara(user_name, username, compliment_text, is_anonymous):
    try:
        if is_anonymous:
            sender_info = "🎭 Аноним"
        else:
            sender_info = f"👤 {user_name}"
            if username and username != "Пользователь" and username != "Аноним":
                sender_info += f" ({username})"

        message_text = f"""💌 Новый комплимент! ✨

{sender_info}
💝 Текст: {compliment_text}

Спасибо за добрые слова! 💐"""

        bot.send_message(SARA_CHAT_ID, message_text, parse_mode=None)
        print(f"✅ Комплимент отправлен Саре")
        return True

    except Exception as e:
        print(f"❌ Ошибка отправки Саре: {e}")
        return False

def get_compliments_count():
    try:
        with open('compliments.json', 'r', encoding='utf-8') as f:
            compliments = json.load(f)
        return len(compliments)
    except FileNotFoundError:
        return 0

def get_last_compliment_time():
    try:
        with open('compliments.json', 'r', encoding='utf-8') as f:
            compliments = json.load(f)
        if compliments:
            return compliments[-1]['timestamp']
        return "еще нет"
    except FileNotFoundError:
        return "еще нет"

# Установка вебхука при запуске
def set_webhook():
    webhook_url = os.environ.get('RENDER_EXTERNAL_URL') + '/webhook'
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=webhook_url)
        print(f"✅ Вебхук установлен: {webhook_url}")
    except Exception as e:
        print(f"❌ Ошибка установки вебхука: {e}")

if __name__ == '__main__':
    print("💝 Запуск бота комплиментов на Render...")
    set_webhook()
    print("🚀 Бот готов к работе!")
