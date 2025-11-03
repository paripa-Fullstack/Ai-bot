import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import sqlite3
import requests
from datetime import datetime, timedelta
import json
import threading
from admin_web import app as admin_app

def run_flask():
    admin_app.run(host='0.0.0.0', port=5000, debug=False)

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы
BOT_TOKEN = "8341275663:AAGEItYtwThsQsDNK3IxPVPvJ5lLd2as9Cg"
DEEPINFRA_API_KEY = "IAL10Nhs5VTjBrW5JV5AOfrCQ6APliFX"
DEEPINFRA_API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"

# Криптовалютные адреса для оплаты
CRYPTO_ADDRESSES = {
    "TRC20": "THJRTXnaSMnBcHmBy9tveYjinAUb6g8dE2",
    "BTC": "bc1q4rjfy9anukz00m4fz9m0vkqzhh0qwcht0a8yqn"
}

# Цены подписок (в USD)
SUBSCRIPTION_PRICES = {
    "weekly": {"price": 5, "duration_days": 7, "name": "Недельная подписка"},
    "monthly": {"price": 15, "duration_days": 30, "name": "Месячная подписка"},
    "yearly": {"price": 100, "duration_days": 365, "name": "Годовая подписка"}
}

# Состояния для ConversationHandler
PHONE, LOCATION, NAME, WAITING_RECEIPT = range(4)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  last_name TEXT,
                  phone TEXT,
                  location_lat REAL,
                  location_lon REAL,
                  location_address TEXT,
                  name TEXT,
                  registration_date TEXT,
                  trial_uses INTEGER DEFAULT 5,
                  is_subscribed INTEGER DEFAULT 0,
                  subscription_end TEXT,
                  total_requests INTEGER DEFAULT 0)''')
    
    # Таблица платежей
    c.execute('''CREATE TABLE IF NOT EXISTS payments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  subscription_type TEXT,
                  payment_date TEXT,
                  receipt_file_id TEXT,
                  approved INTEGER DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    # Таблица истории запросов
    c.execute('''CREATE TABLE IF NOT EXISTS request_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  request_text TEXT,
                  response_text TEXT,
                  request_date TEXT,
                  FOREIGN KEY (user_id) REFERENCES users(user_id))''')
    
    conn.commit()
    conn.close()

# Проверка доступа пользователя
def check_user_access(user_id):
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("SELECT trial_uses, is_subscribed, subscription_end FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return False, "Пользователь не зарегистрирован"
    
    trial_uses, is_subscribed, subscription_end = result
    
    # Проверка подписки
    if is_subscribed and subscription_end:
        if datetime.fromisoformat(subscription_end) > datetime.now():
            return True, "Активная подписка"
        else:
            # Подписка истекла
            conn = sqlite3.connect('bot_users.db')
            c = conn.cursor()
            c.execute("UPDATE users SET is_subscribed = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
    
    # Проверка пробных использований
    if trial_uses > 0:
        return True, f"Пробный период ({trial_uses} использований осталось)"
    
    return False, "Нет доступа"

# Уменьшение количества пробных использований
def decrease_trial_uses(user_id):
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET trial_uses = trial_uses - 1, total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Увеличение счетчика запросов
def increase_request_count(user_id):
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# Запрос к DeepInfra API
def query_deepinfra(prompt, user_id):
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "messages": [
            {"role": "system", "content": "Ты полезный AI-ассистент, который помогает пользователям с любыми вопросами. Отвечай подробно, профессионально и дружелюбно на русском языке."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(DEEPINFRA_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        ai_response = result['choices'][0]['message']['content']
        
        # Сохранение в историю
        conn = sqlite3.connect('bot_users.db')
        c = conn.cursor()
        c.execute("INSERT INTO request_history (user_id, request_text, response_text, request_date) VALUES (?, ?, ?, ?)",
                  (user_id, prompt, ai_response, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return ai_response
    except Exception as e:
        logger.error(f"Ошибка API DeepInfra: {e}")
        return f"❌ Произошла ошибка при обработке запроса: {str(e)}"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Проверка регистрации
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing_user = c.fetchone()
    conn.close()
    
    if existing_user:
        await update.message.reply_text(
            f"🎉 С возвращением, {user.first_name}!\n\n"
            "Используйте команды:\n"
            "/help - Помощь по боту\n"
            "/status - Ваш статус подписки\n"
            "/subscribe - Оформить подписку\n\n"
            "Просто отправьте мне любой вопрос, и я отвечу!"
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🚀 *Добро пожаловать в AI Premium Bot!*\n\n"
        "🤖 Это самый мощный AI-ассистент в Telegram!\n\n"
        "✨ *Что я умею:*\n"
        "• Отвечаю на любые вопросы с помощью передовой AI-модели\n"
        "• Помогаю с программированием и техническими задачами\n"
        "• Создаю тексты, статьи, посты для соцсетей\n"
        "• Перевожу тексты на любые языки\n"
        "• Решаю математические задачи\n"
        "• Даю советы и рекомендации\n"
        "• Генерирую идеи для бизнеса и творчества\n\n"
        "🎁 *БОНУС:* 5 бесплатных запросов для новых пользователей!\n\n"
        "Для начала работы, пожалуйста, поделитесь своим номером телефона 📱",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return PHONE

# Обработка номера телефона
async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact:
        context.user_data['phone'] = contact.phone_number
        context.user_data['user_id'] = update.effective_user.id
        context.user_data['username'] = update.effective_user.username
        context.user_data['first_name'] = update.effective_user.first_name
        context.user_data['last_name'] = update.effective_user.last_name
        
        await update.message.reply_text(
            "✅ Отлично! Теперь поделитесь своим местоположением 📍",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("📍 Поделиться местоположением, для обработки нужно подождать!", request_location=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return LOCATION
    else:
        await update.message.reply_text("❌ Пожалуйста, используйте кнопку для отправки номера телефона.")
        return PHONE

# Обработка местоположения
async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    if location:
        context.user_data['location_lat'] = location.latitude
        context.user_data['location_lon'] = location.longitude
        
        await update.message.reply_text(
            "✅ Отлично! Последний шаг - напишите ваше имя:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Пропустить")]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return NAME
    else:
        await update.message.reply_text("❌ Пожалуйста, используйте кнопку для отправки местоположения.")
        return LOCATION

# Обработка имени
async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    
    if name == "Пропустить":
        name = context.user_data.get('first_name', 'Пользователь')
    
    context.user_data['name'] = name
    
    # Сохранение в базу данных
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("""INSERT INTO users 
                 (user_id, username, first_name, last_name, phone, location_lat, location_lon, name, registration_date)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (context.user_data['user_id'], context.user_data.get('username'), 
               context.user_data.get('first_name'), context.user_data.get('last_name'),
               context.user_data['phone'], context.user_data['location_lat'], 
               context.user_data['location_lon'], name, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"🎉 *Регистрация завершена, {name}!*\n\n"
        "✅ У вас есть *5 бесплатных запросов*!\n\n"
        "💬 Просто напишите мне любой вопрос, и я отвечу.\n\n"
        "📊 Используйте:\n"
        "/status - Проверить статус\n"
        "/subscribe - Оформить подписку\n"
        "/help - Помощь",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("❓ Помощь"), KeyboardButton("📊 Мой статус")]],
            resize_keyboard=True
        )
    )
    return ConversationHandler.END

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 *AI Premium Bot - Команды*

*Основные команды:*
/start - Начать работу с ботом
/help - Показать это сообщение
/status - Проверить статус подписки
/subscribe - Оформить подписку
/history - История ваших запросов (последние 10)

*Как использовать бота:*
Просто напишите мне любой вопрос, и я отвечу!

*Примеры запросов:*
• "Напиши статью про искусственный интеллект"
• "Как создать сайт на Python?"
• "Переведи текст на английский: Привет, как дела?"
• "Объясни квантовую физику простыми словами"
• "Дай совет по инвестициям"

*Тарифы:*
🎁 5 бесплатных запросов для новых пользователей
💎 Недельная подписка - $5 (безлимит на 7 дней)
💎 Месячная подписка - $15 (безлимит на 30 дней)
💎 Годовая подписка - $100 (безлимит на 365 дней)

По вопросам поддержки: @yoursupportAI
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Команда /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("""SELECT trial_uses, is_subscribed, subscription_end, total_requests, registration_date 
                 FROM users WHERE user_id = ?""", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        await update.message.reply_text("❌ Вы не зарегистрированы. Используйте /start")
        return
    
    trial_uses, is_subscribed, subscription_end, total_requests, registration_date = result
    
    status_text = f"📊 *Ваш статус*\n\n"
    status_text += f"👤 ID: `{user_id}`\n"
    status_text += f"📅 Дата регистрации: {registration_date[:10]}\n"
    status_text += f"📈 Всего запросов: {total_requests}\n\n"
    
    if is_subscribed and subscription_end:
        sub_end = datetime.fromisoformat(subscription_end)
        if sub_end > datetime.now():
            days_left = (sub_end - datetime.now()).days
            status_text += f"✅ *Активная подписка*\n"
            status_text += f"⏳ Осталось дней: {days_left}\n"
            status_text += f"📆 Действует до: {subscription_end[:10]}\n"
        else:
            status_text += f"❌ Подписка истекла: {subscription_end[:10]}\n"
            status_text += f"🎁 Пробных запросов: {trial_uses}\n"
    else:
        status_text += f"🎁 Пробных запросов осталось: {trial_uses}/5\n"
    
    if trial_uses == 0 and (not is_subscribed or datetime.fromisoformat(subscription_end) <= datetime.now()):
        status_text += "\n💎 Оформите подписку: /subscribe"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')

# Команда /subscribe
async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💎 Неделя - $5", callback_data='sub_weekly')],
        [InlineKeyboardButton("💎 Месяц - $15", callback_data='sub_monthly')],
        [InlineKeyboardButton("💎 Год - $100", callback_data='sub_yearly')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "💎 *Выберите подписку:*\n\n"
        "🔹 *Недельная* - $5 (безлимитный доступ на 7 дней)\n"
        "🔹 *Месячная* - $15 (безлимитный доступ на 30 дней)\n"
        "🔹 *Годовая* - $100 (безлимитный доступ на 365 дней)\n\n"
        "После оплаты отправьте скриншот чека для активации!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Обработка выбора подписки
async def subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    sub_type = query.data.replace('sub_', '')
    sub_info = SUBSCRIPTION_PRICES[sub_type]
    
    payment_text = f"""
💳 *Оплата подписки: {sub_info['name']}*

💵 Цена: ${sub_info['price']}
⏳ Срок: {sub_info['duration_days']} дней

*Выберите способ оплаты:*

🔹 *TRC20 (USDT):*
`{CRYPTO_ADDRESSES['TRC20']}`

🔹 *Bitcoin (BTC):*
`{CRYPTO_ADDRESSES['BTC']}`

*Инструкция:*
1. Переведите ${sub_info['price']} на один из адресов выше
2. Сделайте скриншот транзакции
3. Отправьте скриншот в этот чат

⚠️ После проверки платежа администратором ваша подписка будет активирована! По вопросам поддержки: @yoursupportAI     
    """
    
    context.user_data['pending_subscription'] = sub_type
    
    await query.edit_message_text(payment_text, parse_mode='Markdown')

# Обработка чеков об оплате
async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        return
    
    user_id = update.effective_user.id
    
    if 'pending_subscription' not in context.user_data:
        await update.message.reply_text(
            "❌ Сначала выберите подписку через /subscribe"
        )
        return
    
    photo = update.message.photo[-1]
    file_id = photo.file_id
    sub_type = context.user_data['pending_subscription']
    
    # Сохранение платежа в БД
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("""INSERT INTO payments (user_id, subscription_type, payment_date, receipt_file_id)
                 VALUES (?, ?, ?, ?)""",
              (user_id, sub_type, datetime.now().isoformat(), file_id))
    payment_id = c.lastrowid
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ Спасибо! Ваш чек получен.\n\n"
        f"🔍 ID платежа: `{payment_id}`\n\n"
        f"Ваша подписка будет активирована после проверки администратором.\n"
        f"Это обычно занимает до 24 часов.\n\n"
        f"Пожалуйста, сохраните ID платежа для связи с поддержкой. @yoursupportAI",
        parse_mode='Markdown'
    )
    
    # Уведомление администратора (замените YOUR_ADMIN_ID на ваш ID)
    # await context.bot.send_photo(
    #     chat_id=YOUR_ADMIN_ID,
    #     photo=file_id,
    #     caption=f"💳 Новый платеж!\n\nUser ID: {user_id}\nPayment ID: {payment_id}\nПодписка: {sub_type}\n\nДля активации используйте:\n/approve {payment_id}"
    # )

# Команда /history
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("""SELECT request_text, request_date FROM request_history 
                 WHERE user_id = ? ORDER BY id DESC LIMIT 10""", (user_id,))
    history = c.fetchall()
    conn.close()
    
    if not history:
        await update.message.reply_text("📭 История запросов пуста.")
        return
    
    history_text = "📜 *Ваши последние 10 запросов:*\n\n"
    for idx, (request, date) in enumerate(history, 1):
        date_str = datetime.fromisoformat(date).strftime("%d.%m.%Y %H:%M")
        request_preview = request[:50] + "..." if len(request) > 50 else request
        history_text += f"{idx}. _{date_str}_\n{request_preview}\n\n"
    
    await update.message.reply_text(history_text, parse_mode='Markdown')

# Обработка текстовых сообщений (запросы к AI)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Проверка специальных кнопок
    if user_message == "❓ Помощь":
        await help_command(update, context)
        return
    elif user_message == "📊 Мой статус":
        await status_command(update, context)
        return
    
    # Проверка доступа
    has_access, access_message = check_user_access(user_id)
    
    if not has_access:
        await update.message.reply_text(
            "❌ У вас закончились бесплатные запросы!\n\n"
            "💎 Оформите подписку для безлимитного доступа:\n"
            "/subscribe\n\n"
            "📊 Проверить статус: /status"
        )
        return
    
    # Отправка "печатает..."
    await update.message.chat.send_action(action="typing")
    
    # Отправка сообщения о начале генерации
    status_message = await update.message.reply_text(
        "🤖 *Нейросеть думает...*\n"
        "⏳ Генерирую ответ, пожалуйста подождите...",
        parse_mode='Markdown'
    )
    
    # Запрос к AI
    response = query_deepinfra(user_message, user_id)
    
    # Удаление статусного сообщения
    try:
        await status_message.delete()
    except:
        pass
    
    # Уменьшение пробных использований или увеличение счетчика
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute("SELECT is_subscribed, subscription_end FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        is_subscribed, subscription_end = result
        if is_subscribed and subscription_end and datetime.fromisoformat(subscription_end) > datetime.now():
            increase_request_count(user_id)
        else:
            decrease_trial_uses(user_id)
            
            # Проверка оставшихся использований
            conn = sqlite3.connect('bot_users.db')
            c = conn.cursor()
            c.execute("SELECT trial_uses FROM users WHERE user_id = ?", (user_id,))
            remaining = c.fetchone()[0]
            conn.close()
            
            if remaining > 0:
                response += f"\n\n_Осталось бесплатных запросов: {remaining}/5_"
            else:
                response += f"\n\n⚠️ _Это был ваш последний бесплатный запрос! Оформите подписку: /subscribe_"
    
    # Отправка ответа
    try:
        await update.message.reply_text(response, parse_mode='Markdown')
    except:
        await update.message.reply_text(response)

# Команда отмены регистрации
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Регистрация отменена. Для повторной регистрации используйте /start"
    )
    return ConversationHandler.END

def main():
    # Инициализация базы данных
    init_db()
    flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()
logger.info("🌐 Веб-админка запущена на порту 5000")
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # ConversationHandler для регистрации
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, phone_handler)],
            LOCATION: [MessageHandler(filters.LOCATION, location_handler)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Добавление обработчиков
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CallbackQueryHandler(subscription_callback, pattern='^sub_'))
    application.add_handler(MessageHandler(filters.PHOTO, receipt_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    # Запуск бота
    logger.info("🤖 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
