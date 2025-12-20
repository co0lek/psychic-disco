import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

BOT_TOKEN = os.environ["TELEGRAM_TOKEN"]

CHAT_IDS = [
    os.environ["CHAT_ID"],
    os.environ.get("CHAT_ID_WIFE"),
]

INSTRUMENTS = [
    {
        "ticker": "LQDT",
        "board": "TQTF",
        "name": "Ликвидность",
        "buy_price": 1.8630,
        "quantity": 585780,
    },
    {
        "ticker": "RU000A108ZB2",
        "board": "TQIF",
        "name": "2хОФЗ",
        "buy_price": 153650.0,
        "quantity": 2,  # как ты уточнил
    },
    {
        "ticker": "RU000A0JR2C1",
        "board": "TQIF",
        "name": "ВИМ Казначейский",
        "buy_price": 103.45,
        "quantity": 9660,
    },
    {
        "ticker": "OBLG",
        "board": "TQTF",
        "name": "Российские облигации",
        "buy_price": 187.1,
        "quantity": 5335,
    },
]

MOEX_URL = (
    "https://iss.moex.com/iss/engines/stock/markets/shares/"
    "boards/{board}/securities/{ticker}.json"
    "?iss.meta=off&iss.only=marketdata"
)


def get_price(instrument):
    url = MOEX_URL.format(
        board=instrument["board"],
        ticker=instrument["ticker"],
    )
    r = requests.get(url, timeout=10).json()

    marketdata = r.get("marketdata", {})
    data = marketdata.get("data", [])
    columns = marketdata.get("columns", [])

    if not data:
        return None

    row = data[0]

    def col(name):
        return row[columns.index(name)] if name in columns else None

    price = col("WAPRICE") or col("LAST") or col("MARKETPRICE")
    prev = col("PREVPRICE")

    return price, prev


def build_message():
    tz = ZoneInfo("Europe/Moscow")
    now = datetime.now(tz)

    lines = [
        "📊 Цены фондов",
        now.strftime("%d.%m.%Y %H:%M"),
        "",
    ]

    total_value = 0.0
    total_buy = 0.0

    for inst in INSTRUMENTS:
        result = get_price(inst)

        name = inst["name"]
        ticker = inst["ticker"]
        qty = inst["quantity"]
        buy_price = inst["buy_price"]

        lines.append(f"*{name}* (`{ticker}`)")

        if result is None:
            lines.append("нет торговых данных")
            lines.append("")
            continue

        price, prev = result

        value = price * qty
        buy_value = buy_price * qty

        total_value += value
        total_buy += buy_value

        lines.append(f"Цена пая: {price:,.4f} ₽")
        lines.append(f"Количество паёв: {qty:,}".replace(",", " "))

        if prev:
            delta = price - prev
            delta_pct = delta / prev * 100
            lines.append(
                f"За день: {delta:+.4f} ₽ ({delta_pct:+.2f}%)"
            )
        else:
            lines.append("За день: нет данных")

        total_delta = value - buy_value
        total_delta_pct = total_delta / buy_value * 100

        lines.append(
            f"С покупки (всего): {total_delta:+,.2f} ₽ ({total_delta_pct:+.2f}%)"
        )
        lines.append("")

    if total_buy > 0:
        total_delta = total_value - total_buy
        total_delta_pct = total_delta / total_buy * 100

        lines.extend([
            "💼 Итого по портфелю",
            f"Стоимость: {total_value:,.2f} ₽",
            f"Результат: {total_delta:+,.2f} ₽ ({total_delta_pct:+.2f}%)",
        ])

    return "\n".join(lines)


def send_message(text):
    for chat_id in CHAT_IDS:
        if not chat_id:
            continue

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )


def main():
    message = build_message()
    send_message(message)


if __name__ == "__main__":
    main()
