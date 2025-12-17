import requests
from datetime import datetime
import os
import time

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

FUNDS = {
    "RU000A108ZB2": "2x ОФЗ",
    "LQDT": "Ликвидность",
}

def get_prices(ticker):
    """Получение цены ПИФа с MOEX"""
    url = f"https://iss.moex.com/iss/engines/fund/markets/unitfund/securities/{ticker}.json?iss.meta=off&iss.only=marketdata"

    try:
        r = requests.get(url, timeout=10).json()
    except Exception:
        return None, None

    marketdata = r.get("marketdata", {})
    rows = marketdata.get("data")
    cols = marketdata.get("columns")

    if not rows or not cols:
        return None, None

    data = rows[0]

    # Поле LAST — последняя цена, CHANGE — изменение
    try:
        last = data[cols.index("LAST")]
        change = data[cols.index("CHANGE")]

        if last is None or change is None:
            return None, None

        prev = last - change  # предыдущая цена
    except Exception:
        return None, None

    return last, prev


def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })


def build_message():
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    lines = [f"📊 Цены фондов\n{now}\n"]

    for ticker, name in FUNDS.items():
        last, prev = get_prices(ticker)

        if last is None or prev is None:
            lines.append(f"{name} ({ticker})\nнет торговых данных\n")
            continue

        change = ((last - prev) / prev) * 100
        sign = "+" if change >= 0 else ""

        lines.append(
            f"{name} ({ticker})\n"
            f"Цена: {last:.2f} ₽\n"
            f"Изменение за день: {sign}{change:.2f}%\n"
        )

        time.sleep(0.3)  # небольшой таймаут, чтобы не перегружать сервер

    return "\n".join(lines)


def main():
    text = build_message()
    send_message(text)


if __name__ == "__main__":
    main()
