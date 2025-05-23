import os
import sqlite3
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DB_PATH = '/home/reijiii/telegram_bot/create.db/db/event_status.db'


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--start-maximized')
    return webdriver.Chrome(options=chrome_options)


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
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
                source TEXT,
                title TEXT,
                description TEXT,
                link_text TEXT,
                link_url TEXT,
                event_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


def save_status_to_db(status):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO status (status) VALUES (?)", (status,))
            conn.commit()
            print(f"🎟️ Статус '{status}' сохранён в таблицу status.")
    except Exception as e:
        print(f"❌ Ошибка записи статуса в БД: {e}")


def insert_event_if_new(event):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT COUNT(*) FROM events
                WHERE title = ? AND source = ?
            ''', (event['title'], event['source']))
            exists = c.fetchone()[0]
            if not exists:
                c.execute('''
                    INSERT INTO events (source, title, description, link_text, link_url, event_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    event['source'], event['title'], event['description'],
                    event['link_text'], event['link_url'], event['event_date']
                ))
                conn.commit()
                print(f"🆕 Добавлено новое событие: {event['title']} ({event['source']})")
            else:
                print(f"⏩ Уже существует: {event['title']} ({event['source']})")
    except Exception as e:
        print(f"❌ Ошибка вставки события: {e}")


def parse_single_event():
    try:
        driver = create_driver()
        driver.get("https://www.etihadarena.ae/en/event-booking/2025-turkish-airlines-euroleague-f4")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'btn-cta-golden'))
        )
        button_text = driver.find_element(By.CLASS_NAME, 'btn-cta-golden') \
                            .find_element(By.TAG_NAME, 'a').text.strip()
        status = "BUY TICKETS" if button_text == "BUY TICKETS" else "SOLD OUT"
        save_status_to_db(status)
    except Exception as e:
        print(f"❌ Ошибка при парсинге Euroleague: {e}")
    finally:
        driver.quit()


def parse_yas_island():
    try:
        driver = create_driver()
        driver.get('https://www.yasisland.com/en/events')
        time.sleep(5)  # Лучше заменить на WebDriverWait

        # Новый селектор для реальных карточек
        cards = driver.find_elements(By.CSS_SELECTOR, 'li.yas-feature-tile-wrapper')
        print(f"🔍 Найдено карточек Yas Island: {len(cards)}")

        for card in cards:
            try:
                title = card.find_element(By.CSS_SELECTOR, 'h3').text.strip()
                description = card.find_element(By.CSS_SELECTOR, '.card-description p').text.strip()
                date = card.find_element(By.CSS_SELECTOR, '.card-location p').text.strip()
                link_elem = card.find_element(By.CSS_SELECTOR, '.card-cta a')
                link_text = link_elem.text.strip()
                link_url = link_elem.get_attribute('href')

                # Обработка относительных ссылок
                if link_url and not link_url.startswith("http"):
                    link_url = "https://www.yasisland.com" + link_url

                event = {
                    'source': 'Yas Island',
                    'title': title,
                    'description': description,
                    'link_text': link_text,
                    'link_url': link_url,
                    'event_date': date
                }

                insert_event_if_new(event)

            except Exception as e:
                print(f"⚠️ Ошибка в карточке Yas Island: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка Yas Island: {e}")
    finally:
        driver.quit()


def insert_or_update_event(event):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT title, description, link_text, event_date FROM events WHERE link_url = ?",
                   (event['link_url'],))
    existing = cursor.fetchone()

    if existing:
        title_db, description_db, link_text_db, event_date_db = existing

        # Проверяем, изменилось ли что-то
        if (event['title'] != title_db or
                event['description'] != description_db or
                event['link_text'] != link_text_db or
                event['event_date'] != event_date_db):

            cursor.execute("""
                UPDATE events
                SET title = ?, description = ?, link_text = ?, event_date = ?
                WHERE link_url = ?
            """, (
                event['title'],
                event['description'],
                event['link_text'],
                event['event_date'],
                event['link_url']
            ))
            print(f"🔄 Обновлено событие: {event['title']}")
        else:
            print(f"🟰 Без изменений: {event['title']}")

    else:
        cursor.execute("""
            INSERT INTO events (source, title, description, link_text, link_url, event_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event['source'],
            event['title'],
            event['description'],
            event['link_text'],
            event['link_url'],
            event['event_date']
        ))
        print(f"✅ Добавлено новое событие: {event['title']}")

    conn.commit()
    conn.close()


def parse_etihad_arena():
    try:
        driver = create_driver()
        driver.get('https://www.etihadarena.ae/en/events')
        time.sleep(3)

        cards = driver.find_elements(By.CLASS_NAME, 'editorial-item')
        print(f"🔍 Найдено карточек Etihad Arena: {len(cards)}")

        current_urls = []

        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, 'gridTitle').text.strip()
                description = card.find_element(By.CLASS_NAME, 'descriptions').text.strip()

                # Поиск ссылки глубже (на случай вложенности)
                try:
                    link_elem = card.find_element(By.CSS_SELECTOR, 'a[href]')
                    link_text = link_elem.text.strip()
                    link_url = link_elem.get_attribute('href')
                except:
                    link_text = ''
                    link_url = ''

                current_urls.append(link_url)

                try:
                    event_date = card.find_element(By.CLASS_NAME, 'editorial-item--title').text.strip()
                except:
                    event_date = ''

                event = {
                    'source': 'Etihad Arena',
                    'title': title,
                    'description': description,
                    'link_text': link_text,
                    'link_url': link_url,
                    'event_date': event_date
                }

                insert_or_update_event(event)

            except Exception as e:
                print(f"⚠️ Ошибка в карточке Etihad Arena: {e}")

        # Удаление устаревших событий
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT link_url FROM events WHERE source = ?", ('Etihad Arena',))
        saved_urls = [row[0] for row in cursor.fetchall()]

        for url in saved_urls:
            if url not in current_urls:
                cursor.execute("DELETE FROM events WHERE link_url = ?", (url,))
                print(f"🗑️ Удалено устаревшее событие Etihad Arena: {url}")

        conn.commit()

        conn.close()

    except Exception as e:
        print(f"⚠️ Ошибка при извлечении событий с Etihad Arena: {e}")
    finally:
        driver.quit()




def main_loop():
    init_db()
    try:
        while True:
            parse_single_event()
            parse_etihad_arena()
            parse_yas_island()
            print("⏳ Ожидание 60 секунд...\n")
            time.sleep(60)
    except KeyboardInterrupt:
        print("🛑 Остановлено пользователем.")


if __name__ == '__main__':
    main_loop()

