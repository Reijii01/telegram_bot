import sqlite3
import os

# Путь к базе
DB_PATH = 'db/event_status.db'


def create_db():
    # Удаляем старую таблицу, если она существует
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Создаем таблицу с новой колонкой updated_at
    c.execute('''
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Вставляем тестовый статус
    c.execute("INSERT INTO status (status) VALUES (?)", ("Тестовый статус",))

    conn.commit()
    print("✅ База создана и тестовая запись добавлена!")

    # Читаем последний статус
    c.execute(
        "SELECT id, status, created_at, updated_at FROM status ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    print(
        f"📋 Последняя запись в базе: ID={row[0]}, Статус='{row[1]}', Дата создания={row[2]}, Дата обновления={row[3]}")

    conn.close()


if __name__ == '__main__':
    create_db()
