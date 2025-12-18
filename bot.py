import requests
import os
from datetime import datetime, timezone, timedelta
import time

# === НАСТРОЙКИ ===

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MARKET = "shares"
BOARD = "TQTF"

# ⬇⬇⬇ ЗДЕСЬ ВЫ ЯВНО УКАЗЫВАЕТЕ ТИКЕРЫ ⬇⬇⬇
TICKERS = [
    "LQDT",
]

# =======================================


def build_url(ticker: str) -> str:
    """
    ЯВНО формируем URL из тикера
    """
    url = (
        "https://iss.moex.com/iss/"
        f"engines/stock/"
        f"markets/{MARKET}/"
        f"boards/{BOARD}/"
        f"securities/{ticker}.json"
        "?iss.meta=off&iss.only=marketdata"
    )
    return url


def get_price(ticker: str):
    url = build_url(ticker)

    print("REQUEST URL:", url)

    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    marketdata = data.get("marketdata", {})
    columns = marketdata.get("columns", [])
    rows = marketdata.get("data", [])

    if not rows or not columns:
        return None, None

    row = rows[0]

    def get_field(name):
        if name in columns:
            return row[columns.index(name)]
        return None

    # Основная цена — последняя сделка или текущая рыночная
    price = (
        get_field("LAST")
        or get_field("MARKETPRICE")
        or get_field("LCURRENTPRICE")
        or get_field("CLOSEPRICE")
    )

    # База для сравнения (вчера)
    base = (
        get_field("PREVPRICE")
        or get_field("LCLOSEPRICE")
        or get_field("MARKETPRICETODAY")
    )

    if price is None or base is None:
        return None, None

    return float(price), float(base)

def send_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text
    })


def main():
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk).strftime("%d.%m.%Y %H:%M")

    lines = [f"📊 Цены фондов\n{now}\n"]

    for ticker in TICKERS:
        last, prev = get_price(ticker)

        if last is None or prev is None:
            lines.append(f"{ticker}\nнет торговых данных\n")
            continue

        change = ((last - prev) / prev) * 100
        sign = "+" if change >= 0 else ""

        lines.append(
            f"{ticker}\n"
            f"Цена: {last:.4f} ₽\n"
            f"Изменение за день: {sign}{change:.2f}%\n"
        )

        time.sleep(0.3)

    send_message("\n".join(lines))


if __name__ == "__main__":
    main()
