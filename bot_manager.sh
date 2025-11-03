#!/bin/bash

# ============================================
# Скрипт для запуска и мониторинга AI Bot
# ============================================

BOT_SCRIPT="ai_telegram_bot.py"
BOT_NAME="ai_telegram_bot"
PYTHON="python3"
LOG_FILE="bot.log"
PID_FILE="bot.pid"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода логов
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Проверка, запущен ли бот
is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Запуск бота
start_bot() {
    if is_running; then
        warning "Бот уже запущен (PID: $(cat $PID_FILE))"
        return 1
    fi
    
    log "Запуск бота..."
    
    # Проверка наличия файла
    if [ ! -f "$BOT_SCRIPT" ]; then
        error "Файл $BOT_SCRIPT не найден!"
        return 1
    fi
    
    # Проверка зависимостей
    if ! $PYTHON -c "import telegram" 2>/dev/null; then
        error "Библиотека python-telegram-bot не установлена!"
        info "Установите: pip install -r requirements.txt"
        return 1
    fi
    
    # Запуск в фоне
    nohup $PYTHON $BOT_SCRIPT >> $LOG_FILE 2>&1 &
    echo $! > $PID_FILE
    
    sleep 2
    
    if is_running; then
        log "✅ Бот успешно запущен (PID: $(cat $PID_FILE))"
        return 0
    else
        error "Не удалось запустить бота. Проверьте логи: tail -f $LOG_FILE"
        return 1
    fi
}

# Остановка бота
stop_bot() {
    if ! is_running; then
        warning "Бот не запущен"
        return 1
    fi
    
    pid=$(cat "$PID_FILE")
    log "Остановка бота (PID: $pid)..."
    
    kill $pid
    sleep 2
    
    # Принудительная остановка, если не остановился
    if ps -p $pid > /dev/null 2>&1; then
        warning "Принудительная остановка..."
        kill -9 $pid
    fi
    
    rm -f "$PID_FILE"
    log "✅ Бот остановлен"
}

# Перезапуск бота
restart_bot() {
    log "Перезапуск бота..."
    stop_bot
    sleep 2
    start_bot
}

# Статус бота
status_bot() {
    echo ""
    echo "=========================================="
    echo "     📊 СТАТУС AI TELEGRAM BOT"
    echo "=========================================="
    echo ""
    
    if is_running; then
        pid=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ Статус: ЗАПУЩЕН${NC}"
        echo "🆔 PID: $pid"
        
        # Время работы процесса
        start_time=$(ps -p $pid -o lstart= 2>/dev/null)
        echo "🕐 Запущен: $start_time"
        
        # Использование памяти
        mem=$(ps -p $pid -o rss= 2>/dev/null)
        mem_mb=$((mem / 1024))
        echo "💾 Память: ${mem_mb}MB"
        
        # CPU
        cpu=$(ps -p $pid -o %cpu= 2>/dev/null)
        echo "⚡ CPU: ${cpu}%"
        
    else
        echo -e "${RED}❌ Статус: ОСТАНОВЛЕН${NC}"
    fi
    
    echo ""
    echo "📁 Файлы:"
    echo "   Скрипт: $BOT_SCRIPT"
    echo "   Логи: $LOG_FILE"
    echo "   БД: bot_users.db"
    
    # Размер базы данных
    if [ -f "bot_users.db" ]; then
        db_size=$(du -h bot_users.db | cut -f1)
        echo "   Размер БД: $db_size"
    fi
    
    # Последние 3 строки лога
    if [ -f "$LOG_FILE" ]; then
        log_size=$(du -h $LOG_FILE | cut -f1)
        echo "   Размер лога: $log_size"
        echo ""
        echo "📝 Последние записи лога:"
        echo "=========================================="
        tail -n 3 $LOG_FILE
    fi
    
    echo "=========================================="
    echo ""
}

# Просмотр логов
logs_bot() {
    if [ ! -f "$LOG_FILE" ]; then
        warning "Файл логов не найден"
        return 1
    fi
    
    log "Показываю логи (Ctrl+C для выхода)..."
    tail -f $LOG_FILE
}

# Очистка логов
clear_logs() {
    if [ -f "$LOG_FILE" ]; then
        log "Очистка логов..."
        > $LOG_FILE
        log "✅ Логи очищены"
    else
        warning "Файл логов не найден"
    fi
}

# Бэкап базы данных
backup_db() {
    if [ ! -f "bot_users.db" ]; then
        error "База данных не найдена!"
        return 1
    fi
    
    backup_dir="backups"
    mkdir -p $backup_dir
    
    backup_file="$backup_dir/bot_users_$(date +%Y%m%d_%H%M%S).db"
    
    log "Создание бэкапа базы данных..."
    cp bot_users.db $backup_file
    
    if [ -f "$backup_file" ]; then
        log "✅ Бэкап создан: $backup_file"
        
        # Оставляем только последние 10 бэкапов
        ls -t $backup_dir/bot_users_*.db | tail -n +11 | xargs -r rm
        info "Хранится последних бэкапов: $(ls $backup_dir/bot_users_*.db 2>/dev/null | wc -l)"
    else
        error "Не удалось создать бэкап!"
        return 1
    fi
}

# Обновление зависимостей
update_deps() {
    log "Обновление зависимостей..."
    
    if [ ! -f "requirements.txt" ]; then
        error "Файл requirements.txt не найден!"
        return 1
    fi
    
    pip install --upgrade -r requirements.txt
    
    if [ $? -eq 0 ]; then
        log "✅ Зависимости обновлены"
    else
        error "Ошибка обновления зависимостей"
        return 1
    fi
}

# Мониторинг (автоперезапуск при падении)
monitor_bot() {
    log "🔍 Запуск мониторинга бота..."
    log "Бот будет автоматически перезапускаться при падении"
    log "Нажмите Ctrl+C для остановки мониторинга"
    
    while true; do
        if ! is_running; then
            error "Бот остановлен! Перезапуск через 5 секунд..."
            sleep 5
            start_bot
        fi
        sleep 30  # Проверка каждые 30 секунд
    done
}

# Установка автозапуска через systemd
install_service() {
    log "Установка systemd сервиса..."
    
    service_file="/etc/systemd/system/${BOT_NAME}.service"
    current_dir=$(pwd)
    
    sudo bash -c "cat > $service_file" <<EOF
[Unit]
Description=AI Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$current_dir
ExecStart=$PYTHON $current_dir/$BOT_SCRIPT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable $BOT_NAME.service
    
    log "✅ Сервис установлен!"
    info "Управление сервисом:"
    info "  sudo systemctl start $BOT_NAME"
    info "  sudo systemctl stop $BOT_NAME"
    info "  sudo systemctl status $BOT_NAME"
}

# Меню
show_menu() {
    echo ""
    echo "=========================================="
    echo "     🤖 AI TELEGRAM BOT - УПРАВЛЕНИЕ"
    echo "=========================================="
    echo ""
    echo "1. 🚀 Запустить бота"
    echo "2. 🛑 Остановить бота"
    echo "3. 🔄 Перезапустить бота"
    echo "4. 📊 Статус бота"
    echo "5. 📝 Показать логи (live)"
    echo "6. 🗑️  Очистить логи"
    echo "7. 💾 Создать бэкап БД"
    echo "8. 📦 Обновить зависимости"
    echo "9. 🔍 Мониторинг (автоперезапуск)"
    echo "10. ⚙️  Установить systemd сервис"
    echo "0. ❌ Выход"
    echo ""
    echo "=========================================="
}

# Основная функция
main() {
    if [ "$1" ]; then
        case $1 in
            start)
                start_bot
                ;;
            stop)
                stop_bot
                ;;
            restart)
                restart_bot
                ;;
            status)
                status_bot
                ;;
            logs)
                logs_bot
                ;;
            backup)
                backup_db
                ;;
            monitor)
                monitor_bot
                ;;
            *)
                error "Неизвестная команда: $1"
                echo "Доступные команды: start, stop, restart, status, logs, backup, monitor"
                exit 1
                ;;
        esac
    else
        # Интерактивное меню
        while true; do
            show_menu
            read -p "Выберите действие: " choice
            
            case $choice in
                1) start_bot ;;
                2) stop_bot ;;
                3) restart_bot ;;
                4) status_bot ;;
                5) logs_bot ;;
                6) clear_logs ;;
                7) backup_db ;;
                8) update_deps ;;
                9) monitor_bot ;;
                10) install_service ;;
                0) 
                    log "Выход..."
                    exit 0
                    ;;
                *)
                    error "Неверный выбор!"
                    ;;
            esac
            
            if [ "$choice" != "5" ] && [ "$choice" != "9" ]; then
                read -p "Нажмите Enter для продолжения..."
            fi
        done
    fi
}

# Запуск
main "$@"
