import asyncio
import sqlite3
import os
import time

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

DB_PATH = '/root/telegram_watcher/telegram_bot/create.db/db/event_status.db'


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('start-maximized')
    chrome_options.add_argument('disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    return webdriver.Chrome(options=chrome_options)


def save_status_to_db(status):
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
    c.execute("INSERT INTO status (status) VALUES (?)", (status,))
    conn.commit()
    conn.close()


def insert_event_if_new(conn, event):
    c = conn.cursor()
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


def parse_single_event(driver):
    try:
        driver.get("https://www.etihadarena.ae/en/event-booking/2025-turkish-airlines-euroleague-f4")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(10)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'btn-cta-golden'))
        )
        button_block = driver.find_element(By.CLASS_NAME, 'btn-cta-golden')
        button_text = button_block.find_element(By.TAG_NAME, 'a').text.strip()

        status = "BUY TICKETS" if button_text == "BUY TICKETS" else "SOLD OUT"
        save_status_to_db(status)
        print(f"🎟️ Статус '{status}' сохранён в таблицу status.")
    except Exception as e:
        print(f"❌ Ошибка при парсинге Euroleague: {e}")


async def parse_yas_island(driver, conn):
    driver.get('https://www.yasisland.com/en/events')
    await asyncio.sleep(3)
    try:
        cards = driver.find_elements(By.CLASS_NAME, 'tile--card')
        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, 'tile__title').text
                description = card.find_element(By.CLASS_NAME, 'tile__text').text
                link_elem = card.find_element(By.TAG_NAME, 'a')
                link_text = link_elem.text
                link_url = link_elem.get_attribute('href')
                event = {
                    'source': 'Yas Island',
                    'title': title,
                    'description': description,
                    'link_text': link_text,
                    'link_url': link_url,
                    'event_date': ''
                }
                insert_event_if_new(conn, event)
            except Exception as e:
                print(f"⚠️ Ошибка в карточке Yas Island: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка Yas Island: {e}")


async def parse_etihad_arena(driver, conn):
    driver.get('https://www.etihadarena.ae/en/events')
    await asyncio.sleep(3)
    try:
        cards = driver.find_elements(By.CLASS_NAME, 'event-card')
        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, 'event-card__title').text
                description = card.find_element(By.CLASS_NAME, 'event-card__description').text
                link_elem = card.find_element(By.TAG_NAME, 'a')
                link_text = link_elem.text
                link_url = link_elem.get_attribute('href')
                event = {
                    'source': 'Etihad Arena',
                    'title': title,
                    'description': description,
                    'link_text': link_text,
                    'link_url': link_url,
                    'event_date': ''
                }
                insert_event_if_new(conn, event)
            except Exception as e:
                print(f"⚠️ Ошибка в карточке Etihad: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка Etihad: {e}")


async def parse_ticketmaster(driver, conn):
    driver.get('https://www.ticketmaster.ae')
    await asyncio.sleep(3)
    try:
        container = driver.find_element(By.CSS_SELECTOR, '[data-testid="eventList"]')
        cards = container.find_elements(By.CLASS_NAME, 'sc-3a43054f-4')
        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, 'sc-3a43054f-9').text
                description = card.find_element(By.CLASS_NAME, 'sc-3a43054f-13').text
                link_elem = card.find_element(By.TAG_NAME, 'a')
                link_url = link_elem.get_attribute('href')
                event_date = card.find_element(By.CLASS_NAME, 'sc-3a43054f-12').text
                event = {
                    'source': 'Ticketmaster',
                    'title': title,
                    'description': description,
                    'link_text': '',
                    'link_url': link_url,
                    'event_date': event_date
                }
                insert_event_if_new(conn, event)
            except Exception as e:
                print(f"⚠️ Ошибка в карточке Ticketmaster: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка eventList: {e}")


async def main_loop():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    driver = create_driver()
    conn = sqlite3.connect(DB_PATH)
    driver_start_time = time.time()

    try:
        while True:
            now = time.time()

            if now - driver_start_time > 43200:
                print("🔄 Перезапуск драйвера после 12 часов...")
                driver.quit()
                driver = create_driver()
                driver_start_time = time.time()

            # Парсинг одного события (статуса)
            parse_single_event(driver)

            # Парсинг всех событий
            await parse_yas_island(driver, conn)
            await parse_etihad_arena(driver, conn)
            await parse_ticketmaster(driver, conn)

            print("⏳ Ожидание 60 секунд...\n")
            await asyncio.sleep(60)
    finally:
        driver.quit()
        conn.close()


if __name__ == '__main__':
    asyncio.run(main_loop())
