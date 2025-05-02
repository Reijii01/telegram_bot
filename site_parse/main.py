import os
import sqlite3
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


def parse_single_event(driver):
    try:
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


def parse_yas_island(driver):
    try:
        driver.get('https://www.yasisland.com/en/events')
        time.sleep(3)
        cards = driver.find_elements(By.CLASS_NAME, 'card-wrapper')
        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, 'card-title').text.strip()
                description = card.find_element(By.CLASS_NAME, 'card-description').text.strip()
                link_elem = card.find_element(By.CLASS_NAME, 'card-cta').find_element(By.TAG_NAME, 'a')
                link_text = link_elem.text.strip()
                link_url = link_elem.get_attribute('href')
                if link_url and not link_url.startswith("http"):
                    link_url = "https://www.yasisland.com" + link_url

                event = {
                    'source': 'Yas Island',
                    'title': title,
                    'description': description,
                    'link_text': link_text,
                    'link_url': link_url,
                    'event_date': ''
                }
                insert_event_if_new(event)
            except Exception as e:
                print(f"⚠️ Ошибка в карточке Yas Island: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка Yas Island: {e}")



def parse_etihad_arena(driver):
    try:
        driver.get('https://www.etihadarena.ae/en/events')
        time.sleep(3)

        # Извлекаем все карточки событий
        cards = driver.find_elements(By.CLASS_NAME, 'editorial-item')

        for card in cards:
            try:
                # Извлекаем дату события
                event_date = card.find_element(By.CLASS_NAME, 'editorial-item--title').text.strip()

                # Извлекаем название события
                title = card.find_element(By.CLASS_NAME, 'gridTitle').text.strip()

                # Извлекаем описание события
                description = card.find_element(By.CLASS_NAME, 'descriptions').text.strip()

                # Извлекаем ссылку на событие
                link_elem = card.find_element(By.CLASS_NAME, 'btn-primary')
                link_text = link_elem.text.strip()  # Кнопка "BUY TICKETS"
                link_url = link_elem.get_attribute('href')

                event = {
                    'source': 'Etihad Arena',
                    'title': title,
                    'description': description,
                    'link_text': link_text,
                    'link_url': link_url,
                    'event_date': event_date
                }

                insert_event_if_new(event)

            except Exception as e:
                print(f"⚠️ Ошибка в карточке Etihad: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка при извлечении событий с Etihad: {e}")


def parse_ticketmaster(driver):
    try:
        driver.get('https://www.ticketmaster.ae')
        time.sleep(3)
        container = driver.find_element(By.CSS_SELECTOR, '[data-testid="eventList"]')
        cards = container.find_elements(By.CLASS_NAME, 'sc-3a43054f-4')
        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, 'sc-3a43054f-9').text
                description = card.find_element(By.CLASS_NAME, 'sc-3a43054f-13').text
                link_elem = card.find_element(By.TAG_NAME, 'a')
                event_date = card.find_element(By.CLASS_NAME, 'sc-3a43054f-12').text
                event = {
                    'source': 'Ticketmaster',
                    'title': title,
                    'description': description,
                    'link_text': '',
                    'link_url': link_elem.get_attribute('href'),
                    'event_date': event_date
                }
                insert_event_if_new(event)
            except Exception as e:
                print(f"⚠️ Ошибка в карточке Ticketmaster: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка eventList: {e}")


def main_loop():
    init_db()
    driver = create_driver()
    driver_start_time = time.time()

    try:
        while True:
            if time.time() - driver_start_time > 43200:
                print("🔄 Перезапуск драйвера после 12 часов...")
                driver.quit()
                driver = create_driver()
                driver_start_time = time.time()

            parse_single_event(driver)
            parse_yas_island(driver)
            parse_etihad_arena(driver)
            parse_ticketmaster(driver)

            print("⏳ Ожидание 60 секунд...\n")
            time.sleep(60)

    except KeyboardInterrupt:
        print("🛑 Остановлено пользователем.")
    finally:
        driver.quit()


if __name__ == '__main__':
    main_loop()
