import os
import requests
from datetime import datetime, timezone, timedelta

# ================== НАСТРОЙКИ ==================

INSTRUMENTS = [
    {
        "ticker": "LQDT",
        "board": "TQTF",
        "name": "Ликвидность",
        "buy_price": 1.8630,  # ← укажите цену покупки или None
    },
    {
        "ticker": "RU000A108ZB2",
        "board": "TQIF",
        "name": "2хОФЗ",
        "buy_price": 153650,
    },
    {
        "ticker": "RU000A0JR2C1",
        "board": "TQIF",
        "name": "ВИМ Казначейский",
        "buy_price": 103.45,
    },
    {
        "ticker": "OBLG",
        "board": "TQTF",
        "name": "Российские облигации",
        "buy_price": 187.1,
    },
]

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_IDS = [
    os.environ["CHAT_ID"],
    os.environ.get("CHAT_ID_WIFE"),
]

MOEX_URL_TEMPLATE = (
    "https://iss.moex.com/iss/engines/stock/markets/shares/"
    "boards/{board}/securities/{ticker}.json"
    "?iss.meta=off&iss.only=marketdata"
)

MSK_TZ = timezone(timedelta(hours=3))

# ================== ЛОГИКА ==================

def fetch_marketdata(ticker: str, board: str):
    url = MOEX_URL_TEMPLATE.format(ticker=ticker, board=board)
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json().get("marketdata", {})
    columns = data.get("columns", [])
    rows = data.get("data", [])
    if not rows:
        return None
    return dict(zip(columns, rows[0]))


def format_price_change(change, percent):
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.4f} ₽ ({sign}{percent:.2f}%)"


def build_message():
    now_msk = datetime.now(MSK_TZ).strftime("%d.%m.%Y %H:%M")
    lines = [f"📊 Цены фондов\n{now_msk}\n"]

    for inst in INSTRUMENTS:
        ticker = inst["ticker"]
        board = inst["board"]
        name = inst["name"]
        buy_price = inst.get("buy_price")

        lines.append(f"{name} ({ticker})")

        try:
            md = fetch_marketdata(ticker, board)
            if not md or md.get("WAPRICE") is None:
                lines.append("нет торговых данных\n")
                continue

            price = float(md["WAPRICE"])
            lines.append(f"Цена: {price:.4f} ₽")

            day_change = md.get("WAPTOPREVWAPRICE")
            day_percent = md.get("WAPTOPREVWAPRICEPRCNT")

            if day_change is not None and day_percent is not None:
                lines.append(
                    "Изменение за день: "
                    + format_price_change(float(day_change), float(day_percent))
                )
            else:
                lines.append("Изменение за день: нет данных")

            if buy_price:
                diff = price - buy_price
                diff_pct = diff / buy_price * 100
                sign = "+" if diff > 0 else ""
                lines.append(
                    f"С покупки: {sign}{diff:.4f} ₽ ({sign}{diff_pct:.2f}%)"
                )

            lines.append("")

        except Exception as e:
            lines.append(f"ошибка получения данных\n")

    return "\n".join(lines).strip()


def send_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        if not chat_id:
            continue
        requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
            },
            timeout=10,
        )


def main():
    message = build_message()
    send_message(message)


if __name__ == "__main__":
    main()
