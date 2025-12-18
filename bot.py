import requests
from datetime import datetime
import os
import time

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MARKET = "shares"
BOARD = "TQTF"

FUNDS = {
    "WIM2OFZ": "2x ОФЗ",
}

def get_prices(ticker):
    url = (
        f"https://iss.moex.com/iss/engines/stock/markets/{MARKET}/"
        f"boards/{BOARD}/securities/{ticker}.json"
        f"?iss.meta=off&iss.only=marketdata"
    )

    try:
        r = requests.get(url, timeout=10).json()
    except Exception:
        return None, None

    marketdata = r.get("marketdata", {})
    rows = marketdata.get("data")
    cols = marketdata.get("columns")

    if not rows or not cols:
        return None, None

    if "LAST" not in cols or "PREVPRICE" not in cols:
        return None, None

    data = rows[0]

    last = data[cols.index("LAST")]
    prev = data[cols.index("PREVPRICE")]

    if last is None or prev is None:
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

        time.sleep(0.3)

    return "\n".join(lines)


def main():
    text = build_message()
    send_message(text)


if __name__ == "__main__":
    main()
