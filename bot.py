import requests
from datetime import datetime
import os
import time

# =========================
# НАСТРОЙКИ
# =========================
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MARKET = "shares"
BOARD = "TQTF"

# Список фондов: тикер -> название
FUNDS = {
    "WIM2OFZ": "2x ОФЗ",
    # можно добавить ещё
    # "SBGB": "Сбер ОФЗ",
}

# =========================
# ПОЛУЧЕНИЕ ЦЕН
# =========================
def get_prices(ticker):
    url = (
        f"https://iss.moex.com/iss/engines/stock/markets/{MARKET}/"
        f"boards/{BOARD}/securities/{ticker}.json"
        f"?iss.meta=off&iss.only=marketdata"
    )

    r = requests.get(url, timeout=10).json()
    data = r["marketdata"]["data"][0]
    cols = r["marketdata"]["columns"]

    last = data[cols.index("LAST")]
    prev = data[cols.index("PREVPRICE")]

    return last, prev

# =========================
# TELEGRAM
# =========================
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    requests.post(url, json=payload, timeout=10)

# =========================
# ФОРМИРОВАНИЕ СООБЩЕНИЯ
# =========================
def build_message():
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    lines = [f"📊 Цены фондов\n{now}\n"]

    for ticker, name in FUNDS.items():
        last, prev = get_prices(ticker)

        if last is None or prev is None:
            lines.append(f"{name} ({ticker})\nнет данных\n")
            continue

        change = ((last - prev) / prev) * 100
        sign = "+" if change >= 0 else ""

        lines.append(
            f"{name} ({ticker})\n"
            f"Цена: {last:.2f} ₽\n"
            f"Изменение за день: {sign}{change:.2f}%\n"
        )

        time.sleep(0.3)

    return "\n".join(lines)

# =========================
# ОСНОВНОЙ ЗАПУСК
# =========================
def main():
    text = build_message()
    send_message(text)

if __name__ == "__main__":
    main()
