#!/usr/bin/env python3
"""
Скрипт для массовой рассылки сообщений пользователям бота
"""
import sqlite3
import asyncio
from telegram import Bot
from datetime import datetime

BOT_TOKEN = "8113704562:AAEmoJn4sOE9XE53bX1jZj25pKjiWpN3oiE"

def get_users(filter_type="all"):
    """
    Получить список пользователей по фильтру
    filter_type: "all", "subscribed", "trial", "expired"
    """
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    
    if filter_type == "all":
        c.execute("SELECT user_id, username, first_name FROM users")
    elif filter_type == "subscribed":
        c.execute("""SELECT user_id, username, first_name FROM users 
                     WHERE is_subscribed = 1 AND subscription_end > ?""", 
                  (datetime.now().isoformat(),))
    elif filter_type == "trial":
        c.execute("""SELECT user_id, username, first_name FROM users 
                     WHERE trial_uses > 0 AND (is_subscribed = 0 OR subscription_end <= ?)""", 
                  (datetime.now().isoformat(),))
    elif filter_type == "expired":
        c.execute("""SELECT user_id, username, first_name FROM users 
                     WHERE trial_uses = 0 AND (is_subscribed = 0 OR subscription_end <= ?)""", 
                  (datetime.now().isoformat(),))
    
    users = c.fetchall()
    conn.close()
    return users

async def send_broadcast(message_text, filter_type="all", delay=0.1):
    """
    Отправить сообщение всем пользователям
    """
    bot = Bot(token=BOT_TOKEN)
    users = get_users(filter_type)
    
    print(f"\n📤 Начинаем рассылку для {len(users)} пользователей...")
    print(f"🎯 Фильтр: {filter_type}")
    print("-" * 50)
    
    success_count = 0
    fail_count = 0
    blocked_count = 0
    
    for user_id, username, first_name in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode='Markdown'
            )
            print(f"✅ Отправлено: {user_id} (@{username or 'N/A'})")
            success_count += 1
            await asyncio.sleep(delay)  # Задержка между отправками
            
        except Exception as e:
            error_msg = str(e)
            if "blocked" in error_msg.lower() or "bot was blocked" in error_msg.lower():
                print(f"🚫 Заблокирован: {user_id} (@{username or 'N/A'})")
                blocked_count += 1
            else:
                print(f"❌ Ошибка {user_id}: {error_msg}")
                fail_count += 1
    
    print("-" * 50)
    print(f"\n📊 Результаты рассылки:")
    print(f"✅ Успешно: {success_count}")
    print(f"🚫 Заблокировали: {blocked_count}")
    print(f"❌ Ошибки: {fail_count}")
    print(f"📈 Всего: {len(users)}")

def show_menu():
    print("\n" + "="*50)
    print("📤 МАССОВАЯ РАССЫЛКА")
    print("="*50)
    print("\nВыберите тип получателей:")
    print("1. 👥 Все пользователи")
    print("2. 💎 Только с активной подпиской")
    print("3. 🎁 Только на пробном периоде")
    print("4. ❌ Только с истекшим доступом")
    print("0. ⬅️ Назад")
    print("="*50)

def get_message_templates():
    return {
        "1": """
🎉 *Специальное предложение!*

Оформите годовую подписку со скидкой 30%!

💎 Было: $100
💎 Сейчас: $70

Предложение действует только 48 часов! ⏰

Оформить: /subscribe
        """,
        "2": """
🆕 *Новые возможности бота!*

Мы добавили новые функции:
• Улучшенные ответы AI
• Поддержка изображений
• Более быстрая обработка запросов

Попробуйте прямо сейчас! 🚀
        """,
        "3": """
🎁 *Бонус для наших пользователей!*

Приведи друга и получи +10 бесплатных запросов!

Просто отправь ему ссылку на бота: @ваш_бот

Чем больше друзей - тем больше бонусов! 🎉
        """,
        "4": """
⚠️ *Ваша подписка скоро закончится!*

Не забудьте продлить подписку, чтобы не потерять доступ к AI-ассистенту.

Продлить: /subscribe

Специальное предложение при продлении! 💎
        """
    }

def main():
    print("\n🚀 Скрипт массовой рассылки")
    
    show_menu()
    choice = input("\nВыберите получателей: ")
    
    filter_map = {
        "1": "all",
        "2": "subscribed",
        "3": "trial",
        "4": "expired"
    }
    
    filter_type = filter_map.get(choice)
    if not filter_type:
        print("❌ Неверный выбор!")
        return
    
    # Предпросмотр количества получателей
    users = get_users(filter_type)
    print(f"\n📊 Будет отправлено: {len(users)} пользователям")
    
    # Выбор сообщения
    print("\n" + "="*50)
    print("📝 ВЫБОР СООБЩЕНИЯ")
    print("="*50)
    print("\n1. Использовать шаблон")
    print("2. Написать свое сообщение")
    
    msg_choice = input("\nВаш выбор: ")
    
    if msg_choice == "1":
        templates = get_message_templates()
        print("\nШаблоны:")
        print("1. Специальное предложение")
        print("2. Новые возможности")
        print("3. Бонус за приведение друга")
        print("4. Напоминание о продлении")
        
        template_choice = input("\nВыберите шаблон: ")
        message_text = templates.get(template_choice)
        
        if not message_text:
            print("❌ Неверный выбор!")
            return
    else:
        print("\nВведите текст сообщения (для завершения введите 'END' на новой строке):")
        lines = []
        while True:
            line = input()
            if line == "END":
                break
            lines.append(line)
        message_text = "\n".join(lines)
    
    # Предпросмотр
    print("\n" + "="*50)
    print("👀 ПРЕДПРОСМОТР СООБЩЕНИЯ")
    print("="*50)
    print(message_text)
    print("="*50)
    
    confirm = input("\n✅ Отправить это сообщение? (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ Отменено")
        return
    
    # Задержка между сообщениями
    delay_input = input("\nЗадержка между сообщениями в секундах (по умолчанию 0.1): ")
    try:
        delay = float(delay_input) if delay_input else 0.1
    except:
        delay = 0.1
    
    # Запуск рассылки
    print("\n🚀 Запуск рассылки...")
    asyncio.run(send_broadcast(message_text, filter_type, delay))
    print("\n✅ Рассылка завершена!")

if __name__ == '__main__':
    main()
