import logging
import os

# Создание директории для логов, если её нет
log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(log_dir, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # Минимальный уровень логирования
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'telegram_bot.log')),  # Лог для telegram_bot.py
        logging.StreamHandler()  # Лог в консоль
    ]
)

# Пример логирования
logging.info("Старт Telegram-бота")

# В коде можно заменить print на логирование
logging.info("Бот запущен и работает...")

# Пример обработки ошибок
try:
    # Твой код...
    pass
except Exception as e:
    logging.error(f"Ошибка: {e}")
