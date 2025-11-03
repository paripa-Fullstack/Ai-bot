# 💾 SQL ЗАПРОСЫ ДЛЯ УПРАВЛЕНИЯ БОТОМ

## 📊 Просмотр данных

### Все пользователи

```sql
SELECT 
    user_id,
    username,
    phone,
    trial_uses,
    is_subscribed,
    subscription_end,
    total_requests,
    registration_date
FROM users
ORDER BY registration_date DESC;
```

### Активные подписки

```sql
SELECT 
    user_id,
    username,
    phone,
    subscription_end,
    total_requests
FROM users
WHERE is_subscribed = 1 
AND subscription_end > datetime('now')
ORDER BY subscription_end DESC;
```

### Пользователи на пробном периоде

```sql
SELECT 
    user_id,
    username,
    phone,
    trial_uses,
    registration_date
FROM users
WHERE trial_uses > 0 
AND (is_subscribed = 0 OR subscription_end <= datetime('now'))
ORDER BY registration_date DESC;
```

### Истекшие подписки

```sql
SELECT 
    user_id,
    username,
    phone,
    subscription_end,
    trial_uses
FROM users
WHERE trial_uses = 0 
AND (is_subscribed = 0 OR subscription_end <= datetime('now'))
ORDER BY subscription_end DESC;
```

### Все платежи

```sql
SELECT 
    p.id,
    p.user_id,
    u.username,
    p.subscription_type,
    p.payment_date,
    p.approved,
    u.phone
FROM payments p
LEFT JOIN users u ON p.user_id = u.user_id
ORDER BY p.payment_date DESC;
```

### Неодобренные платежи

```sql
SELECT 
    p.id AS payment_id,
    p.user_id,
    u.username,
    u.phone,
    p.subscription_type,
    p.payment_date,
    p.receipt_file_id
FROM payments p
LEFT JOIN users u ON p.user_id = u.user_id
WHERE p.approved = 0
ORDER BY p.payment_date DESC;
```

---

## 📈 Статистика

### Общая статистика

```sql
SELECT 
    (SELECT COUNT(*) FROM users) AS total_users,
    (SELECT COUNT(*) FROM users WHERE is_subscribed = 1 AND subscription_end > datetime('now')) AS active_subscriptions,
    (SELECT COUNT(*) FROM users WHERE trial_uses > 0) AS trial_users,
    (SELECT SUM(total_requests) FROM users) AS total_requests,
    (SELECT COUNT(*) FROM payments WHERE approved = 0) AS pending_payments,
    (SELECT COUNT(*) FROM payments WHERE approved = 1) AS approved_payments;
```

### Регистрации по дням (последние 30 дней)

```sql
SELECT 
    DATE(registration_date) AS date,
    COUNT(*) AS registrations
FROM users
WHERE registration_date >= datetime('now', '-30 days')
GROUP BY DATE(registration_date)
ORDER BY date DESC;
```

### Топ-10 активных пользователей

```sql
SELECT 
    user_id,
    username,
    phone,
    total_requests,
    is_subscribed,
    subscription_end
FROM users
ORDER BY total_requests DESC
LIMIT 10;
```

### Доход по типам подписок

```sql
SELECT 
    subscription_type,
    COUNT(*) AS count,
    CASE subscription_type
        WHEN 'weekly' THEN COUNT(*) * 5
        WHEN 'monthly' THEN COUNT(*) * 15
        WHEN 'yearly' THEN COUNT(*) * 100
    END AS revenue_usd
FROM payments
WHERE approved = 1
GROUP BY subscription_type;
```

### Конверсия trial → paid

```sql
SELECT 
    CAST((SELECT COUNT(*) FROM users WHERE is_subscribed = 1) AS FLOAT) / 
    CAST((SELECT COUNT(*) FROM users) AS FLOAT) * 100 AS conversion_rate_percent;
```

---

## ✏️ Изменение данных

### Активация подписки

```sql
-- Недельная подписка (7 дней)
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+7 days') 
WHERE user_id = USER_ID;

-- Месячная подписка (30 дней)
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+30 days') 
WHERE user_id = USER_ID;

-- Годовая подписка (365 дней)
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+365 days') 
WHERE user_id = USER_ID;
```

### Продление подписки

```sql
-- Продлить на 30 дней от текущей даты окончания
UPDATE users 
SET subscription_end = datetime(subscription_end, '+30 days') 
WHERE user_id = USER_ID;

-- Продлить на 30 дней от текущего момента
UPDATE users 
SET is_subscribed = 1,
    subscription_end = datetime('now', '+30 days') 
WHERE user_id = USER_ID;
```

### Добавить пробные использования

```sql
-- Добавить 5 использований
UPDATE users 
SET trial_uses = trial_uses + 5 
WHERE user_id = USER_ID;

-- Установить конкретное количество
UPDATE users 
SET trial_uses = 10 
WHERE user_id = USER_ID;

-- Сбросить до 5
UPDATE users 
SET trial_uses = 5 
WHERE user_id = USER_ID;
```

### Одобрить платеж и активировать подписку

```sql
-- Одобрить платеж
UPDATE payments 
SET approved = 1 
WHERE id = PAYMENT_ID;

-- Активировать подписку пользователю (замените USER_ID и количество дней)
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+30 days') 
WHERE user_id = (SELECT user_id FROM payments WHERE id = PAYMENT_ID);
```

### Отменить подписку

```sql
UPDATE users 
SET is_subscribed = 0 
WHERE user_id = USER_ID;
```

---

## 🗑️ Удаление данных

### Удалить пользователя и все его данные

```sql
-- Сначала удалить историю запросов
DELETE FROM request_history WHERE user_id = USER_ID;

-- Затем удалить платежи
DELETE FROM payments WHERE user_id = USER_ID;

-- Наконец удалить пользователя
DELETE FROM users WHERE user_id = USER_ID;
```

### Очистить историю запросов пользователя

```sql
DELETE FROM request_history 
WHERE user_id = USER_ID;
```

### Удалить старые записи истории (старше 30 дней)

```sql
DELETE FROM request_history 
WHERE request_date < datetime('now', '-30 days');
```

### Удалить старые одобренные платежи (старше 1 года)

```sql
DELETE FROM payments 
WHERE approved = 1 
AND payment_date < datetime('now', '-1 year');
```

---

## 🔍 Поиск

### Найти пользователя по имени

```sql
SELECT * FROM users 
WHERE username LIKE '%search_term%' 
OR first_name LIKE '%search_term%' 
OR last_name LIKE '%search_term%'
OR name LIKE '%search_term%';
```

### Найти пользователя по телефону

```sql
SELECT * FROM users 
WHERE phone LIKE '%phone_number%';
```

### Найти пользователя по User ID

```sql
SELECT * FROM users 
WHERE user_id = USER_ID;
```

### История запросов пользователя

```sql
SELECT 
    request_text,
    response_text,
    request_date
FROM request_history
WHERE user_id = USER_ID
ORDER BY request_date DESC
LIMIT 50;
```

---

## 🛠️ Обслуживание базы данных

### Оптимизация базы данных

```sql
VACUUM;
```

### Анализ базы данных

```sql
ANALYZE;
```

### Проверка целостности

```sql
PRAGMA integrity_check;
```

### Размер базы данных

```sql
SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();
```

### Информация о таблицах

```sql
-- Список всех таблиц
SELECT name FROM sqlite_master WHERE type='table';

-- Структура таблицы users
PRAGMA table_info(users);

-- Структура таблицы payments
PRAGMA table_info(payments);

-- Структура таблицы request_history
PRAGMA table_info(request_history);
```

---

## 📊 Отчеты

### Отчет о новых пользователях за период

```sql
SELECT 
    DATE(registration_date) AS date,
    COUNT(*) AS new_users
FROM users
WHERE registration_date BETWEEN '2025-01-01' AND '2025-01-31'
GROUP BY DATE(registration_date)
ORDER BY date;
```

### Отчет о платежах за период

```sql
SELECT 
    DATE(payment_date) AS date,
    subscription_type,
    COUNT(*) AS count,
    SUM(CASE subscription_type
        WHEN 'weekly' THEN 5
        WHEN 'monthly' THEN 15
        WHEN 'yearly' THEN 100
    END) AS revenue_usd
FROM payments
WHERE approved = 1
AND payment_date BETWEEN '2025-01-01' AND '2025-01-31'
GROUP BY DATE(payment_date), subscription_type
ORDER BY date;
```

### Отчет об активности пользователей

```sql
SELECT 
    DATE(request_date) AS date,
    COUNT(DISTINCT user_id) AS active_users,
    COUNT(*) AS total_requests
FROM request_history
WHERE request_date >= datetime('now', '-30 days')
GROUP BY DATE(request_date)
ORDER BY date DESC;
```

---

## 🚀 Массовые операции

### Дать всем пользователям +5 использований (промо)

```sql
UPDATE users 
SET trial_uses = trial_uses + 5;
```

### Продлить все активные подписки на 7 дней (бонус)

```sql
UPDATE users 
SET subscription_end = datetime(subscription_end, '+7 days')
WHERE is_subscribed = 1 
AND subscription_end > datetime('now');
```

### Деактивировать истекшие подписки

```sql
UPDATE users 
SET is_subscribed = 0
WHERE is_subscribed = 1 
AND subscription_end <= datetime('now');
```

---

## 📝 Экспорт данных

### Экспорт пользователей в CSV

```sql
.mode csv
.output users_export.csv
SELECT * FROM users;
.output stdout
```

### Экспорт платежей в CSV

```sql
.mode csv
.output payments_export.csv
SELECT * FROM payments;
.output stdout
```

---

## 🔐 Безопасность

### Создать бэкап перед изменениями

```bash
# В терминале:
cp bot_users.db bot_users_backup_$(date +%Y%m%d_%H%M%S).db
```

### Восстановление из бэкапа

```bash
# В терминале:
cp bot_users_backup_TIMESTAMP.db bot_users.db
```

---

## 💡 Полезные советы

### Открыть базу данных

```bash
sqlite3 bot_users.db
```

### Включить режим отображения заголовков

```sql
.headers on
.mode column
```

### Выход из sqlite3

```sql
.quit
```

### Показать все команды sqlite3

```sql
.help
```

---

## 🎯 Примеры использования

### Пример 1: Активация подписки после оплаты

```sql
-- 1. Найти неодобренный платеж
SELECT * FROM payments WHERE approved = 0 ORDER BY payment_date DESC LIMIT 1;

-- 2. Одобрить платеж
UPDATE payments SET approved = 1 WHERE id = 123;

-- 3. Активировать подписку
UPDATE users 
SET is_subscribed = 1, 
    subscription_end = datetime('now', '+30 days') 
WHERE user_id = 456789;
```

### Пример 2: Промо-акция для всех

```sql
-- Дать всем +10 использований
UPDATE users SET trial_uses = trial_uses + 10;

-- Отправить уведомление (через broadcast.py)
```

### Пример 3: Очистка старых данных

```sql
-- Удалить историю старше 90 дней
DELETE FROM request_history 
WHERE request_date < datetime('now', '-90 days');

-- Оптимизировать базу
VACUUM;
```

---

**Сохраните этот файл для быстрого доступа к SQL запросам! 📌**
