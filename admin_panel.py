#!/usr/bin/env python3
"""
Админ-панель для управления AI Telegram Bot
"""
import sqlite3
from datetime import datetime, timedelta
import sys

def connect_db():
    return sqlite3.connect('bot_users.db')

def show_menu():
    print("\n" + "="*50)
    print("🔧 АДМИН-ПАНЕЛЬ AI TELEGRAM BOT")
    print("="*50)
    print("\n1. 📊 Статистика")
    print("2. 👥 Список пользователей")
    print("3. 💳 Список платежей")
    print("4. ✅ Активировать подписку")
    print("5. 🔍 Найти пользователя")
    print("6. 📜 История запросов пользователя")
    print("7. 💰 Одобрить платеж")
    print("8. 🗑️ Удалить пользователя")
    print("9. 🔄 Сбросить пробные использования")
    print("0. ❌ Выход")
    print("="*50)

def show_statistics():
    conn = connect_db()
    c = conn.cursor()
    
    print("\n📊 СТАТИСТИКА БОТА")
    print("-"*50)
    
    # Всего пользователей
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    print(f"👥 Всего пользователей: {total_users}")
    
    # Активные подписки
    c.execute("SELECT COUNT(*) FROM users WHERE is_subscribed = 1 AND subscription_end > ?", 
              (datetime.now().isoformat(),))
    active_subs = c.fetchone()[0]
    print(f"💎 Активных подписок: {active_subs}")
    
    # Пользователи на пробном периоде
    c.execute("SELECT COUNT(*) FROM users WHERE trial_uses > 0 AND (is_subscribed = 0 OR subscription_end <= ?)", 
              (datetime.now().isoformat(),))
    trial_users = c.fetchone()[0]
    print(f"🎁 На пробном периоде: {trial_users}")
    
    # Всего запросов
    c.execute("SELECT SUM(total_requests) FROM users")
    total_requests = c.fetchone()[0] or 0
    print(f"📈 Всего запросов обработано: {total_requests}")
    
    # Неодобренные платежи
    c.execute("SELECT COUNT(*) FROM payments WHERE approved = 0")
    pending_payments = c.fetchone()[0]
    print(f"⏳ Платежей на проверке: {pending_payments}")
    
    # Доход (примерно)
    c.execute("""SELECT subscription_type, COUNT(*) FROM payments 
                 WHERE approved = 1 GROUP BY subscription_type""")
    payments_by_type = c.fetchall()
    
    prices = {"weekly": 5, "monthly": 15, "yearly": 100}
    total_income = sum(prices.get(sub_type, 0) * count for sub_type, count in payments_by_type)
    print(f"💰 Примерный доход: ${total_income}")
    
    # Регистрации по дням (последние 7 дней)
    print("\n📅 Регистрации за последние 7 дней:")
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).date()
        c.execute("SELECT COUNT(*) FROM users WHERE date(registration_date) = ?", (date.isoformat(),))
        count = c.fetchone()[0]
        print(f"   {date}: {count} пользователей")
    
    conn.close()

def list_users():
    conn = connect_db()
    c = conn.cursor()
    
    print("\n👥 СПИСОК ПОЛЬЗОВАТЕЛЕЙ (последние 20)")
    print("-"*100)
    print(f"{'ID':<12} {'Username':<20} {'Телефон':<15} {'Триал':<7} {'Подписка':<10} {'До':<12}")
    print("-"*100)
    
    c.execute("""SELECT user_id, username, phone, trial_uses, is_subscribed, subscription_end 
                 FROM users ORDER BY registration_date DESC LIMIT 20""")
    users = c.fetchall()
    
    for user_id, username, phone, trial_uses, is_subscribed, sub_end in users:
        username = username or "N/A"
        phone = phone[-10:] if phone else "N/A"
        sub_status = "✅" if is_subscribed else "❌"
        sub_end_str = sub_end[:10] if sub_end else "N/A"
        
        print(f"{user_id:<12} {username:<20} {phone:<15} {trial_uses:<7} {sub_status:<10} {sub_end_str:<12}")
    
    conn.close()

def list_payments():
    conn = connect_db()
    c = conn.cursor()
    
    print("\n💳 СПИСОК ПЛАТЕЖЕЙ (последние 20)")
    print("-"*100)
    print(f"{'ID':<6} {'User ID':<12} {'Тип':<10} {'Дата':<20} {'Статус':<10}")
    print("-"*100)
    
    c.execute("""SELECT id, user_id, subscription_type, payment_date, approved 
                 FROM payments ORDER BY payment_date DESC LIMIT 20""")
    payments = c.fetchall()
    
    for payment_id, user_id, sub_type, pay_date, approved in payments:
        status = "✅ Одобрен" if approved else "⏳ На проверке"
        print(f"{payment_id:<6} {user_id:<12} {sub_type:<10} {pay_date[:19]:<20} {status:<10}")
    
    conn.close()

def activate_subscription():
    user_id = input("\n👤 Введите User ID: ")
    
    print("\nВыберите тип подписки:")
    print("1. Неделя (7 дней)")
    print("2. Месяц (30 дней)")
    print("3. Год (365 дней)")
    
    choice = input("Ваш выбор: ")
    
    days_map = {"1": 7, "2": 30, "3": 365}
    days = days_map.get(choice)
    
    if not days:
        print("❌ Неверный выбор!")
        return
    
    conn = connect_db()
    c = conn.cursor()
    
    # Проверка существования пользователя
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        print(f"❌ Пользователь с ID {user_id} не найден!")
        conn.close()
        return
    
    # Активация подписки
    subscription_end = (datetime.now() + timedelta(days=days)).isoformat()
    c.execute("""UPDATE users 
                 SET is_subscribed = 1, subscription_end = ? 
                 WHERE user_id = ?""", (subscription_end, user_id))
    conn.commit()
    conn.close()
    
    print(f"✅ Подписка активирована для пользователя {user_id} на {days} дней!")
    print(f"   Действительна до: {subscription_end[:10]}")

def find_user():
    search = input("\n🔍 Введите User ID или username: ")
    
    conn = connect_db()
    c = conn.cursor()
    
    # Поиск по ID или username
    c.execute("""SELECT user_id, username, first_name, last_name, phone, 
                 location_lat, location_lon, registration_date, trial_uses, 
                 is_subscribed, subscription_end, total_requests 
                 FROM users WHERE user_id = ? OR username = ?""", (search, search))
    user = c.fetchone()
    
    if not user:
        print(f"❌ Пользователь не найден!")
        conn.close()
        return
    
    print("\n" + "="*50)
    print("👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ")
    print("="*50)
    print(f"🆔 User ID: {user[0]}")
    print(f"👤 Username: @{user[1] or 'N/A'}")
    print(f"📝 Имя: {user[2]} {user[3] or ''}")
    print(f"📱 Телефон: {user[4] or 'N/A'}")
    print(f"📍 Координаты: {user[5]}, {user[6]}" if user[5] else "📍 Координаты: N/A")
    print(f"📅 Регистрация: {user[7][:10]}")
    print(f"🎁 Пробных использований: {user[8]}")
    print(f"💎 Подписка: {'✅ Активна' if user[9] else '❌ Неактивна'}")
    print(f"📆 Действует до: {user[10][:10] if user[10] else 'N/A'}")
    print(f"📈 Всего запросов: {user[11]}")
    
    conn.close()

def show_user_history():
    user_id = input("\n👤 Введите User ID: ")
    
    conn = connect_db()
    c = conn.cursor()
    
    c.execute("""SELECT request_text, request_date FROM request_history 
                 WHERE user_id = ? ORDER BY id DESC LIMIT 20""", (user_id,))
    history = c.fetchall()
    
    if not history:
        print(f"❌ История запросов пуста или пользователь не найден!")
        conn.close()
        return
    
    print(f"\n📜 ИСТОРИЯ ЗАПРОСОВ (последние 20)")
    print("-"*80)
    
    for idx, (request, date) in enumerate(history, 1):
        print(f"\n{idx}. [{date[:19]}]")
        print(f"   {request[:150]}{'...' if len(request) > 150 else ''}")
    
    conn.close()

def approve_payment():
    payment_id = input("\n💳 Введите ID платежа: ")
    
    conn = connect_db()
    c = conn.cursor()
    
    # Получение информации о платеже
    c.execute("""SELECT user_id, subscription_type, approved FROM payments WHERE id = ?""", 
              (payment_id,))
    payment = c.fetchone()
    
    if not payment:
        print(f"❌ Платеж с ID {payment_id} не найден!")
        conn.close()
        return
    
    user_id, sub_type, approved = payment
    
    if approved:
        print(f"⚠️ Этот платеж уже одобрен!")
        conn.close()
        return
    
    # Одобрение платежа
    c.execute("UPDATE payments SET approved = 1 WHERE id = ?", (payment_id,))
    
    # Активация подписки
    days_map = {"weekly": 7, "monthly": 30, "yearly": 365}
    days = days_map.get(sub_type, 30)
    
    subscription_end = (datetime.now() + timedelta(days=days)).isoformat()
    c.execute("""UPDATE users 
                 SET is_subscribed = 1, subscription_end = ? 
                 WHERE user_id = ?""", (subscription_end, user_id))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Платеж {payment_id} одобрен!")
    print(f"✅ Подписка активирована для пользователя {user_id} на {days} дней!")

def delete_user():
    user_id = input("\n⚠️ Введите User ID для удаления: ")
    confirm = input(f"❗ Вы уверены? Это удалит ВСЕ данные пользователя {user_id}! (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Отменено")
        return
    
    conn = connect_db()
    c = conn.cursor()
    
    # Удаление из всех таблиц
    c.execute("DELETE FROM request_history WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM payments WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    
    deleted = c.rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        print(f"✅ Пользователь {user_id} и все его данные удалены!")
    else:
        print(f"❌ Пользователь {user_id} не найден!")

def reset_trial():
    user_id = input("\n👤 Введите User ID: ")
    count = input("🎁 Количество пробных использований (по умолчанию 5): ") or "5"
    
    try:
        count = int(count)
    except:
        print("❌ Неверное значение!")
        return
    
    conn = connect_db()
    c = conn.cursor()
    
    c.execute("UPDATE users SET trial_uses = ? WHERE user_id = ?", (count, user_id))
    
    if c.rowcount > 0:
        conn.commit()
        print(f"✅ Пробные использования установлены на {count} для пользователя {user_id}!")
    else:
        print(f"❌ Пользователь {user_id} не найден!")
    
    conn.close()

def main():
    print("\n🚀 Запуск админ-панели...")
    
    # Проверка наличия базы данных
    try:
        conn = connect_db()
        conn.close()
    except:
        print("❌ База данных не найдена! Убедитесь, что бот запущен и создал базу данных.")
        sys.exit(1)
    
    while True:
        show_menu()
        choice = input("\nВыберите действие: ")
        
        if choice == "1":
            show_statistics()
        elif choice == "2":
            list_users()
        elif choice == "3":
            list_payments()
        elif choice == "4":
            activate_subscription()
        elif choice == "5":
            find_user()
        elif choice == "6":
            show_user_history()
        elif choice == "7":
            approve_payment()
        elif choice == "8":
            delete_user()
        elif choice == "9":
            reset_trial()
        elif choice == "0":
            print("\n👋 До свидания!")
            break
        else:
            print("❌ Неверный выбор!")
        
        input("\nНажмите Enter для продолжения...")

if __name__ == '__main__':
    main()
