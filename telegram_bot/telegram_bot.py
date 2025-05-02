import asyncio
import sqlite3
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Путь к базе данных
DB_PATH ='/root/telegram_watcher/telegram_bot/create.db/db/event_status.db'

# Настройки бота
TELEGRAM_TOKEN = '8138626595:AAFu3zUR8HqvZag9j1FYbj9BnQfIqRQR7xg'
GROUP_CHAT_ID = -1002688502308

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение текущего статуса события и времени обновления
def get_event_status():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT status, updated_at FROM status ORDER BY rowid DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    if result:
        status, updated_at = result
        return status, updated_at
    else:
        return None, None

# Хендлер для личных сообщений
async def private_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await update.message.reply_text("🔒 Я работаю только в группе. Следите за обновлениями там!")

# Хендлер команды /start01
async def start01_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        await update.message.reply_text("✅ Бот успешно запущен и мониторит статус событий!")

# Хендлер команды /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        status, updated_at = get_event_status()
        if status:
            # Форматируем дату в красивый вид
            if updated_at:
                dt = datetime.fromisoformat(updated_at)
                updated_str = dt.strftime('%d.%m.%Y %H:%M')
                await update.message.reply_text(f"ℹ️ Текущий статус события: {status}\n🕒 Последнее обновление: {updated_str}")
            else:
                await update.message.reply_text(f"ℹ️ Текущий статус события: {status}")
        else:
            await update.message.reply_text("⚠️ Статус события пока не найден.")

# Функция мониторинга базы данных
async def monitor_db(application: Application):
    await asyncio.sleep(5)  # Ждем чуть-чуть после запуска приложения
    logger.info("🚀 Мониторинг базы данных запущен.")

    last_status, _ = get_event_status()

    # После старта сразу отправляем первое сообщение
    if last_status == "SOLD OUT":
        await application.bot.send_message(chat_id=GROUP_CHAT_ID, text="🔴 Сейчас доступна только кнопка SOLD OUT.")

    while True:
        current_status, _ = get_event_status()

        if last_status == "SOLD OUT" and current_status == "BUY TICKETS":
            await application.bot.send_message(chat_id=GROUP_CHAT_ID, text="🎉 Билеты доступны! Статус изменился на BUY TICKETS!")

        last_status = current_status
        await asyncio.sleep(60)  # Проверка каждую минуту

# Основная функция запуска бота
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Хендлеры
    application.add_handler(CommandHandler("start01", start01_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE, private_message_handler))

    # Фоновая задача мониторинга базы
    application.job_queue.run_once(lambda context: asyncio.create_task(monitor_db(application)), when=0)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()

