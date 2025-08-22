import asyncio
import os
import sqlite3
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()


DB_PATH = '/root/telegram_watcher/telegram_bot/create.db/db/event_status.db'


TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def get_events():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, event_date, updated_at FROM events ORDER BY updated_at DESC")
    results = c.fetchall()
    conn.close()
    return results


async def private_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await update.message.reply_text("🔒 Я работаю только в группе. Следите за обновлениями там!")


async def start01_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        await update.message.reply_text("✅ Бот успешно запущен и мониторит статус событий!")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        status, updated_at = get_event_status()
        if status:
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at)
                    updated_str = dt.strftime('%d.%m.%Y %H:%M')
                except ValueError:
                    updated_str = updated_at
                await update.message.reply_text(f"ℹ️ Текущий статус события: {status}\n🕒 Последнее обновление: {updated_str}")
            else:
                await update.message.reply_text(f"ℹ️ Текущий статус события: {status}")
        else:
            await update.message.reply_text("⚠️ Статус события пока не найден.")


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup']:
        events = get_events()
        if events:
            message = "📅 Список событий:\n"
            for event_id, title, event_date, updated_at in events:
                try:
                    dt = datetime.fromisoformat(event_date)
                    event_time_str = dt.strftime('%d.%m.%Y %H:%M')
                except ValueError:
                    event_time_str = event_date  

                if updated_at:
                    try:
                        dt_updated = datetime.fromisoformat(updated_at)
                        updated_str = dt_updated.strftime('%d.%m.%Y %H:%M')
                    except ValueError:
                        updated_str = updated_at
                    message += f"{title} - {event_time_str}\n🕒 Последнее обновление: {updated_str}\n\n"
                else:
                    message += f"{title} - {event_time_str}\n🕒 Обновление не найдено\n\n"
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("⚠️ События не найдены.")


async def monitor_db(application: Application):
    await asyncio.sleep(5)
    logger.info("🚀 Мониторинг базы данных запущен.")
    last_events = get_events()

    while True:
        current_events = get_events()
       
        if current_events != last_events:
            logger.info("📢 Обновления в событиях.")
            
            for _, title, event_date, _ in current_events:
                await application.bot.send_message(chat_id=CHAT_ID, text=f"Событие обновлено: {title} — Время: {event_date}")
            last_events = current_events
        await asyncio.sleep(60)


def main():
    application = Application.builder().token(TOKEN).build()

    
    application.add_handler(CommandHandler("start01", start01_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("events", events_command))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE, private_message_handler))

    
    application.job_queue.run_once(lambda context: asyncio.create_task(monitor_db(application)), when=0)

    
    application.run_polling()

if __name__ == '__main__':
    main()




