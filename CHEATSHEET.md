# ⚡ ШПАРГАЛКА - БЫСТРЫЕ КОМАНДЫ

## 🚀 ЗАПУСК И УПРАВЛЕНИЕ

### Простой запуск
```bash
python3 ai_telegram_bot.py
```

### Запуск в фоне
```bash
nohup python3 ai_telegram_bot.py > bot.log 2>&1 &
```

### Через менеджер
```bash
./bot_manager.sh start    # Запуск
./bot_manager.sh stop     # Остановка
./bot_manager.sh restart  # Перезапуск
./bot_manager.sh status   # Статус
```

### Мониторинг
```bash
./bot_manager.sh logs     # Логи live
./bot_manager.sh monitor  # Автоперезапуск при падении
```

---

## 🛠️ АДМИНИСТРИРОВАНИЕ

### Админ-панель
```bash
python3 admin_panel.py
```

### Массовая рассылка
```bash
python3 broadcast.py
```

### Проверка процесса
```bash
ps aux | grep ai_telegram_bot
```

### Убить процесс
```bash
pkill -f ai_telegram_bot.py
```

---

## 💾 БАЗА ДАННЫХ

### Открыть БД
```bash
sqlite3 bot_users.db
```

### Включить красивый вывод
```sql
.headers on
.mode column
```

### Выход из sqlite3
```sql
.quit
```

### Бэкап БД
```bash
cp bot_users.db bot_users_backup_$(date +%Y%m%d).db
```

### Оптимизация БД
```bash
sqlite3 bot_users.db "VACUUM;"
```

---

## 👥 ПОЛЬЗОВАТЕЛИ

### Все пользователи
```sql
SELECT user_id, username, phone, trial_uses, is_subscribed 
FROM users ORDER BY registration_date DESC LIMIT 20;
```

### Активные подписки
```sql
SELECT user_id, username, subscription_end 
FROM users 
WHERE is_subscribed = 1 AND subscription_end > datetime('now');
```

### На trial
```sql
SELECT user_id, username, trial_uses 
FROM users 
WHERE trial_uses > 0 AND is_subscribed = 0;
```

### Найти пользователя
```sql
SELECT * FROM users WHERE user_id = 123456789;
SELECT * FROM users WHERE username = 'username';
```

---

## 💳 ПОДПИСКИ

### Активировать подписку (неделя)
```sql
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+7 days') 
WHERE user_id = 123456789;
```

### Активировать подписку (месяц)
```sql
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+30 days') 
WHERE user_id = 123456789;
```

### Активировать подписку (год)
```sql
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+365 days') 
WHERE user_id = 123456789;
```

### Деактивировать подписку
```sql
UPDATE users SET is_subscribed = 0 WHERE user_id = 123456789;
```

### Добавить trial uses
```sql
UPDATE users SET trial_uses = trial_uses + 5 WHERE user_id = 123456789;
```

---

## 💰 ПЛАТЕЖИ

### Неодобренные платежи
```sql
SELECT p.id, p.user_id, u.username, p.subscription_type, p.payment_date
FROM payments p
LEFT JOIN users u ON p.user_id = u.user_id
WHERE p.approved = 0
ORDER BY p.payment_date DESC;
```

### Одобрить платеж
```sql
UPDATE payments SET approved = 1 WHERE id = 123;
```

### Активировать после одобрения
```sql
-- Сначала найти user_id
SELECT user_id FROM payments WHERE id = 123;

-- Потом активировать (замените USER_ID)
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+30 days') 
WHERE user_id = USER_ID;
```

---

## 📊 СТАТИСТИКА

### Общая статистика
```sql
SELECT 
    (SELECT COUNT(*) FROM users) AS total_users,
    (SELECT COUNT(*) FROM users WHERE is_subscribed = 1) AS subscribed,
    (SELECT SUM(total_requests) FROM users) AS total_requests;
```

### Топ пользователей
```sql
SELECT user_id, username, total_requests 
FROM users 
ORDER BY total_requests DESC 
LIMIT 10;
```

### Регистрации по дням
```sql
SELECT DATE(registration_date) AS date, COUNT(*) AS count
FROM users
WHERE registration_date >= datetime('now', '-7 days')
GROUP BY DATE(registration_date);
```

---

## 🔍 ЛОГИ

### Последние логи
```bash
tail -n 50 bot.log
```

### Логи в реальном времени
```bash
tail -f bot.log
```

### Найти ошибки
```bash
grep ERROR bot.log
```

### Очистить логи
```bash
> bot.log
```

---

## 📦 ОБНОВЛЕНИЕ

### Обновить зависимости
```bash
pip3 install --upgrade -r requirements.txt
```

### Перезапустить после обновления
```bash
./bot_manager.sh restart
```

---

## 🔧 УСТАНОВКА

### Установка с нуля
```bash
# 1. Установить Python
sudo apt update
sudo apt install python3 python3-pip -y

# 2. Установить зависимости
pip3 install -r requirements.txt

# 3. Запустить
python3 ai_telegram_bot.py
```

### Сделать скрипты исполняемыми
```bash
chmod +x bot_manager.sh admin_panel.py broadcast.py
```

---

## 🚨 ЭКСТРЕННЫЕ КОМАНДЫ

### Бот завис - убить процесс
```bash
pkill -9 -f ai_telegram_bot
```

### БД заблокирована
```bash
# Остановить бот
./bot_manager.sh stop
sleep 2
# Запустить снова
./bot_manager.sh start
```

### Восстановить из бэкапа
```bash
cp bot_users_backup_YYYYMMDD.db bot_users.db
```

### Сбросить БД (УДАЛИТ ВСЕ ДАННЫЕ!)
```bash
rm bot_users.db
python3 ai_telegram_bot.py
```

---

## 🔐 БЕЗОПАСНОСТЬ

### Создать бэкап перед изменениями
```bash
cp bot_users.db bot_users_backup_$(date +%Y%m%d_%H%M%S).db
```

### Установить права доступа
```bash
chmod 600 bot_users.db
chmod 700 *.py *.sh
```

---

## 📱 BOTFATHER КОМАНДЫ

### Установить описание
```
/setdescription
```

### Установить команды
```
/setcommands

start - 🚀 Начать работу с ботом
help - ❓ Помощь и информация
status - 📊 Мой статус и использование
subscribe - 💎 Оформить подписку
history - 📜 История моих запросов
```

### Установить изображение
```
/setuserpic
```

---

## 🎯 БЫСТРЫЕ SQL СЦЕНАРИИ

### Дать всем бонус +5 использований
```sql
UPDATE users SET trial_uses = trial_uses + 5;
```

### Продлить все активные подписки на неделю
```sql
UPDATE users 
SET subscription_end = datetime(subscription_end, '+7 days')
WHERE is_subscribed = 1 AND subscription_end > datetime('now');
```

### Удалить пользователя и все данные
```sql
DELETE FROM request_history WHERE user_id = 123456789;
DELETE FROM payments WHERE user_id = 123456789;
DELETE FROM users WHERE user_id = 123456789;
```

### Очистить историю старше 30 дней
```sql
DELETE FROM request_history 
WHERE request_date < datetime('now', '-30 days');
VACUUM;
```

---

## 🔄 АВТОЗАПУСК

### Установить как systemd сервис
```bash
./bot_manager.sh
# Выбрать: 10 - Установить systemd сервис
```

### Управление сервисом
```bash
sudo systemctl start ai_telegram_bot
sudo systemctl stop ai_telegram_bot
sudo systemctl restart ai_telegram_bot
sudo systemctl status ai_telegram_bot
```

### Через cron (автоперезапуск)
```bash
crontab -e
# Добавить:
*/5 * * * * cd /path/to/bot && ./bot_manager.sh start
```

---

## 📊 МОНИТОРИНГ

### Проверить работает ли бот
```bash
./bot_manager.sh status
```

### Использование ресурсов
```bash
top -p $(pgrep -f ai_telegram_bot)
```

### Размер БД
```bash
du -h bot_users.db
```

### Размер логов
```bash
du -h bot.log
```

---

## 💡 ПОЛЕЗНЫЕ АЛИАСЫ

Добавьте в `~/.bashrc`:

```bash
# Алиасы для бота
alias bot-start='cd /path/to/bot && ./bot_manager.sh start'
alias bot-stop='cd /path/to/bot && ./bot_manager.sh stop'
alias bot-status='cd /path/to/bot && ./bot_manager.sh status'
alias bot-logs='cd /path/to/bot && tail -f bot.log'
alias bot-db='cd /path/to/bot && sqlite3 bot_users.db'
alias bot-admin='cd /path/to/bot && python3 admin_panel.py'
```

После добавления:
```bash
source ~/.bashrc
```

---

## 🎓 УЗНАТЬ TELEGRAM ID

### Для пользователя
Отправить любое сообщение боту @userinfobot

### Для группы/канала
```python
# В коде бота добавить:
print(f"Chat ID: {update.effective_chat.id}")
```

---

## ⚙️ ИЗМЕНИТЬ НАСТРОЙКИ БОТА

### Изменить цены подписок
В файле `ai_telegram_bot.py` найдите:
```python
SUBSCRIPTION_PRICES = {
    "weekly": {"price": 5, "duration_days": 7},
    "monthly": {"price": 15, "duration_days": 30},
    "yearly": {"price": 100, "duration_days": 365}
}
```

### Изменить количество trial uses
В файле `ai_telegram_bot.py` найдите:
```python
trial_uses INTEGER DEFAULT 5  # Измените на нужное число
```

### Сменить AI модель
В функции `query_deepinfra()` измените:
```python
"model": "meta-llama/Meta-Llama-3.1-70B-Instruct"
```

---

## 🆘 ПОДДЕРЖКА

### Узнать версию Python
```bash
python3 --version
```

### Проверить установленные пакеты
```bash
pip3 list | grep telegram
```

### Проверить порт (если нужно)
```bash
netstat -tulpn | grep python
```

---

**Сохраните этот файл для быстрого доступа! ⚡**

**Все основные команды в одном месте! 🎯**
