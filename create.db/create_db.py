import sqlite3
import os


DB_PATH = '/root/telegram_watcher/telegram_bot/create.db/db/event_status.db'


def create_db():
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,          -- Yas Island / Etihad / Ticketmaster
            title TEXT NOT NULL,
            description TEXT,
            link_text TEXT,
            link_url TEXT,
            event_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_status_updated_at
        AFTER UPDATE ON status
        FOR EACH ROW
        BEGIN
            UPDATE status
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = OLD.id;
        END;
    ''')

    
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_events_updated_at
        AFTER UPDATE ON events
        FOR EACH ROW
        BEGIN
            UPDATE events
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = OLD.id;
        END;
    ''')

    
    c.execute("INSERT INTO status (status) VALUES (?)", ("Тестовый статус",))

    conn.commit()
    print("✅ Таблицы созданы, триггеры установлены и тестовая запись добавлена!")

   
    c.execute("SELECT id, status, created_at, updated_at FROM status ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    print(f"📋 Последняя запись в статусе: ID={row[0]}, Статус='{row[1]}', Дата создания={row[2]}, Дата обновления={row[3]}")

    conn.close()


if __name__ == '__main__':
    create_db()


