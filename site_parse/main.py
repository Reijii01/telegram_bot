import sqlite3
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Путь к базе
DB_PATH = 'db/event_status.db'


# Функция создания драйвера
def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('start-maximized')
    chrome_options.add_argument('disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--headless')  # Без окна

    return webdriver.Chrome(options=chrome_options)

# Функция для добавления статуса в базу
def save_status_to_db(status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute("INSERT INTO status (status) VALUES (?)", (status,))
    conn.commit()
    conn.close()

# Парсинг события
def parse_event(driver):
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

        print(f"✅ Статус '{status}' успешно сохранен в базу данных.")

    except Exception as e:
        print(f"❌ Ошибка при парсинге события: {e}")

# Основной цикл
def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    driver = create_driver()
    driver_start_time = time.time()

    while True:
        current_time = time.time()

        # Проверка: если прошло больше 12 часов (43200 секунд)
        if current_time - driver_start_time > 43200:
            print("🔄 Перезагрузка драйвера после 12 часов работы...")
            driver.quit()
            driver = create_driver()
            driver_start_time = time.time()

        parse_event(driver)

        time.sleep(60)  # Проверка каждую минуту

if __name__ == '__main__':
    main()
