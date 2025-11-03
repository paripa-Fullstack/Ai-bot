from flask import Flask, render_template_string, request, redirect, session, flash
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Генерируем случайный секретный ключ

# ВАЖНО: Измените эти данные!
ADMIN_USERNAME = "paripa"
ADMIN_PASSWORD = "455126"  # ОБЯЗАТЕЛЬНО СМЕНИТЕ!

# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated_function

# Функции работы с БД
def get_db():
    conn = sqlite3.connect('bot_users.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_statistics():
    conn = get_db()
    c = conn.cursor()
    
    stats = {}
    
    # Всего пользователей
    c.execute("SELECT COUNT(*) as count FROM users")
    stats['total_users'] = c.fetchone()['count']
    
    # Активные подписки
    c.execute("SELECT COUNT(*) as count FROM users WHERE is_subscribed = 1 AND subscription_end > ?", 
              (datetime.now().isoformat(),))
    stats['active_subscriptions'] = c.fetchone()['count']
    
    # На пробном периоде
    c.execute("SELECT COUNT(*) as count FROM users WHERE trial_uses > 0 AND (is_subscribed = 0 OR subscription_end <= ?)", 
              (datetime.now().isoformat(),))
    stats['trial_users'] = c.fetchone()['count']
    
    # Всего запросов
    c.execute("SELECT SUM(total_requests) as total FROM users")
    result = c.fetchone()
    stats['total_requests'] = result['total'] if result['total'] else 0
    
    # Неодобренные платежи
    c.execute("SELECT COUNT(*) as count FROM payments WHERE approved = 0")
    stats['pending_payments'] = c.fetchone()['count']
    
    conn.close()
    return stats

# HTML шаблоны
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Вход в админ-панель</title>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
            text-align: center;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 500;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .alert {
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 5px;
            background: #fee;
            color: #c33;
            border: 1px solid #fcc;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 Админ-панель</h1>
        {% if message %}
        <div class="alert">{{ message }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <label>Логин:</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Пароль:</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Войти</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Админ-панель - AI Bot</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #f5f7fa;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 24px; }
        .header .logout {
            float: right;
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            border-radius: 5px;
            transition: background 0.3s;
        }
        .header .logout:hover {
            background: rgba(255,255,255,0.3);
        }
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
        }
        .stat-card .number {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        .stat-card .label {
            color: #666;
            font-size: 14px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }
        .tab {
            padding: 12px 24px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            color: #666;
            transition: all 0.3s;
        }
        .tab.active {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            margin-bottom: -2px;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .card h2 {
            margin-bottom: 20px;
            color: #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }
        .badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-block;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover {
            background: #5568d3;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #218838;
        }
        .form-inline {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .form-inline input,
        .form-inline select {
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="header">
        <a href="/admin/logout" class="logout">Выход</a>
        <h1>🤖 AI Bot - Админ-панель</h1>
    </div>
    
    <div class="container">
        {% if message %}
        <div class="alert alert-{{ message_type }}">{{ message }}</div>
        {% endif %}
        
        <!-- Статистика -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Всего пользователей</div>
                <div class="number">{{ stats.total_users }}</div>
            </div>
            <div class="stat-card">
                <div class="label">Активные подписки</div>
                <div class="number">{{ stats.active_subscriptions }}</div>
            </div>
            <div class="stat-card">
                <div class="label">На пробном периоде</div>
                <div class="number">{{ stats.trial_users }}</div>
            </div>
            <div class="stat-card">
                <div class="label">Всего запросов</div>
                <div class="number">{{ stats.total_requests }}</div>
            </div>
            <div class="stat-card">
                <div class="label">Платежей на проверке</div>
                <div class="number">{{ stats.pending_payments }}</div>
            </div>
        </div>
        
        <!-- Табы -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('users')">👥 Пользователи</button>
            <button class="tab" onclick="showTab('payments')">💳 Платежи</button>
            <button class="tab" onclick="showTab('activate')">✅ Активация</button>
        </div>
        
        <!-- Пользователи -->
        <div id="users" class="tab-content active">
            <div class="card">
                <h2>Последние пользователи</h2>
                <table>
                    <thead>
                        <tr>
                            <th>User ID</th>
                            <th>Username</th>
                            <th>Телефон</th>
                            <th>Trial</th>
                            <th>Подписка</th>
                            <th>Запросов</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for user in users %}
                        <tr>
                            <td>{{ user.user_id }}</td>
                            <td>@{{ user.username or 'N/A' }}</td>
                            <td>{{ user.phone[-10:] if user.phone else 'N/A' }}</td>
                            <td>{{ user.trial_uses }}/5</td>
                            <td>
                                {% if user.is_subscribed and user.subscription_end > now %}
                                <span class="badge badge-success">✅ Активна</span>
                                {% else %}
                                <span class="badge badge-danger">❌ Нет</span>
                                {% endif %}
                            </td>
                            <td>{{ user.total_requests }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Платежи -->
        <div id="payments" class="tab-content">
            <div class="card">
                <h2>Платежи на проверке</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>User ID</th>
                            <th>Тип</th>
                            <th>Дата</th>
                            <th>Действие</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for payment in payments %}
                        <tr>
                            <td>{{ payment.id }}</td>
                            <td>{{ payment.user_id }}</td>
                            <td>
                                {% if payment.subscription_type == 'weekly' %}Неделя ($5)
                                {% elif payment.subscription_type == 'monthly' %}Месяц ($15)
                                {% elif payment.subscription_type == 'yearly' %}Год ($100)
                                {% endif %}
                            </td>
                            <td>{{ payment.payment_date[:16] }}</td>
                            <td>
                                <form method="POST" action="/admin/approve-payment" style="display: inline;">
                                    <input type="hidden" name="payment_id" value="{{ payment.id }}">
                                    <input type="hidden" name="user_id" value="{{ payment.user_id }}">
                                    <input type="hidden" name="subscription_type" value="{{ payment.subscription_type }}">
                                    <button type="submit" class="btn btn-success">✅ Одобрить</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Активация -->
        <div id="activate" class="tab-content">
            <div class="card">
                <h2>Активировать подписку вручную</h2>
                <form method="POST" action="/admin/activate">
                    <div class="form-inline">
                        <input type="number" name="user_id" placeholder="User ID" required>
                        <select name="subscription_type" required>
                            <option value="weekly">Неделя (7 дней)</option>
                            <option value="monthly">Месяц (30 дней)</option>
                            <option value="yearly">Год (365 дней)</option>
                        </select>
                        <button type="submit" class="btn btn-primary">Активировать</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Скрыть все табы
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(c => c.classList.remove('active'));
            
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(t => t.classList.remove('active'));
            
            // Показать выбранный таб
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
'''

# Маршруты
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect('/admin')
        else:
            return render_template_string(LOGIN_TEMPLATE, message='Неверный логин или пароль!')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin')
@login_required
def dashboard():
    conn = get_db()
    c = conn.cursor()
    
    # Получить статистику
    stats = get_statistics()
    
    # Получить последних пользователей
    c.execute("""SELECT user_id, username, phone, trial_uses, is_subscribed, 
                 subscription_end, total_requests 
                 FROM users ORDER BY registration_date DESC LIMIT 20""")
    users = c.fetchall()
    
    # Получить неодобренные платежи
    c.execute("""SELECT id, user_id, subscription_type, payment_date 
                 FROM payments WHERE approved = 0 ORDER BY payment_date DESC""")
    payments = c.fetchall()
    
    conn.close()
    
    message = session.pop('message', None)
    message_type = session.pop('message_type', 'success')
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        stats=stats,
        users=users,
        payments=payments,
        now=datetime.now().isoformat(),
        message=message,
        message_type=message_type
    )

@app.route('/admin/activate', methods=['POST'])
@login_required
def activate_subscription():
    user_id = request.form.get('user_id')
    subscription_type = request.form.get('subscription_type')
    
    days_map = {"weekly": 7, "monthly": 30, "yearly": 365}
    days = days_map.get(subscription_type, 30)
    
    subscription_end = (datetime.now() + timedelta(days=days)).isoformat()
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute("""UPDATE users 
                     SET is_subscribed = 1, subscription_end = ? 
                     WHERE user_id = ?""", (subscription_end, user_id))
        conn.commit()
        
        if c.rowcount > 0:
            session['message'] = f'✅ Подписка активирована для пользователя {user_id} на {days} дней!'
            session['message_type'] = 'success'
        else:
            session['message'] = f'❌ Пользователь {user_id} не найден!'
            session['message_type'] = 'danger'
    except Exception as e:
        session['message'] = f'❌ Ошибка: {str(e)}'
        session['message_type'] = 'danger'
    finally:
        conn.close()
    
    return redirect('/admin')

@app.route('/admin/approve-payment', methods=['POST'])
@login_required
def approve_payment():
    payment_id = request.form.get('payment_id')
    user_id = request.form.get('user_id')
    subscription_type = request.form.get('subscription_type')
    
    days_map = {"weekly": 7, "monthly": 30, "yearly": 365}
    days = days_map.get(subscription_type, 30)
    
    subscription_end = (datetime.now() + timedelta(days=days)).isoformat()
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Одобрить платеж
        c.execute("UPDATE payments SET approved = 1 WHERE id = ?", (payment_id,))
        
        # Активировать подписку
        c.execute("""UPDATE users 
                     SET is_subscribed = 1, subscription_end = ? 
                     WHERE user_id = ?""", (subscription_end, user_id))
        
        conn.commit()
        
        session['message'] = f'✅ Платеж {payment_id} одобрен! Подписка активирована для пользователя {user_id}!'
        session['message_type'] = 'success'
    except Exception as e:
        session['message'] = f'❌ Ошибка: {str(e)}'
        session['message_type'] = 'danger'
    finally:
        conn.close()
    
    return redirect('/admin')

@app.route('/')
def index():
    return redirect('/admin')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
