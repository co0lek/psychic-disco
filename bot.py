import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# Список фондов: название, URL страницы, имя файла для хранения последней цены
FUNDS = [
    {"name": "2x ОФЗ", "url": "https://investfunds.ru/funds/10817/", "file": "10817.txt"},
    {"name": "Фонд 54", "url": "https://investfunds.ru/funds/54/", "file": "54.txt"},
]

DATA_FOLDER = "fund_data"  # папка для хранения последних цен

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def get_latest_nav(fund_url):
    """Получаем последнюю цену пая с HTML страницы investfunds.ru"""
    try:
        r = requests.get(fund_url, timeout=10)
        r.raise_for_status()
    except Exception:
        return None, None

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", class_="history-table")
    if not table:
        return None, None

    row = table.find("tr")
    if not row:
        return None, None

    cols = row.find_all("td")
    if len(cols) < 2:
        return None, None

    date = cols[0].get_text(strip=True)
    nav = cols[1].get_text(strip=True).replace("\u202f", "").replace("₽", "").replace(",", ".")

    try:
        nav_value = float(nav)
    except ValueError:
        return None, None

    return date, nav_value

def read_prev_price(filename):
    path = os.path.join(DATA_FOLDER, filename)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return float(f.read().strip())
        except Exception:
            return None
    return None

def save_price(filename, price):
    path = os.path.join(DATA_FOLDER, filename)
    with open(path, "w") as f:
        f.write(str(price))

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })

def build_message():
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    lines = [f"📊 Цены фондов\n{now}\n"]

    for fund in FUNDS:
        date, nav = get_latest_nav(fund["url"])
        prev_price = read_prev_price(fund["file"])

        if nav is None:
            lines.append(f"{fund['name']}\nНет торговых данных\n")
            continue

        line = f"{fund['name']}\nДата котировки: {date}\nЦена пая: {nav:,.2f} ₽"

        if prev_price is not None:
            change_pct = ((nav - prev_price) / prev_price) * 100
            sign = "+" if change_pct >= 0 else ""
            line += f"\nИзменение за день: {sign}{change_pct:.2f}%"
        else:
            line += "\nИзменение за день: недоступно"

        lines.append(line)
        save_price(fund["file"], nav)

    return "\n\n".join(lines)

def main():
    while True:
        now = datetime.now()
        # Время для отправки: 12:00 и 18:00 МСК
        if now.hour in [12, 18] and now.minute == 0:
            message = build_message()
            send_message(message)
            time.sleep(60)  # подождать минуту, чтобы не отправить повторно в ту же минуту
        time.sleep(10)  # проверка каждые 10 секунд

if __name__ == "__main__":
    main()
