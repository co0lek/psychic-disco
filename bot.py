import os
import requests
from datetime import datetime, timezone, timedelta

# ================== НАСТРОЙКИ ==================

INSTRUMENTS = [ # здесь все записывать
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
        "quantity": 4,
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

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]

CHAT_IDS = [
    os.environ["CHAT_ID"],
    os.environ["CHAT_ID_WIFE"],
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
    md = r.json().get("marketdata", {})
    columns = md.get("columns", [])
    data = md.get("data", [])
    if not data:
        return None
    return dict(zip(columns, data[0]))


def build_message():
    now_msk = datetime.now(MSK_TZ).strftime("%d.%m.%Y %H:%M")
    lines = [f"📊 Цены фондов\n{now_msk}\n"]

    total_invested = 0.0
    total_current = 0.0

    for inst in INSTRUMENTS:
        ticker = inst["ticker"]
        board = inst["board"]
        name = inst["name"]
        buy_price = inst["buy_price"]
        qty = inst["quantity"]

        lines.append(f"{name} ({ticker})")

        try:
            md = fetch_marketdata(ticker, board)
            if not md or md.get("WAPRICE") is None:
                lines.append("нет торговых данных\n")
                continue

            price = float(md["WAPRICE"])
            lines.append(f"Цена пая: {price:.4f} ₽")
            lines.append(f"Количество паёв: {qty}")

            # --- за день ---
            day_abs = md.get("WAPTOPREVWAPRICE")
            day_pct = md.get("WAPTOPREVWAPRICEPRCNT")
            if day_abs is not None and day_pct is not None:
                sign = "+" if day_abs > 0 else ""
                lines.append(
                    f"За день: {sign}{float(day_abs):.4f} ₽ "
                    f"({sign}{float(day_pct):.2f}%)"
                )
            else:
                lines.append("За день: нет данных")

            # --- по позиции ---
            invested = buy_price * qty
            current = price * qty
            total_invested += invested
            total_current += current

            profit = current - invested
            profit_pct = profit / invested * 100
            sign = "+" if profit >= 0 else ""

            lines.append(
                f"С покупки (всего): {sign}{profit:,.2f} ₽ "
                f"({sign}{profit_pct:.2f}%)"
            )

            lines.append("")

        except Exception:
            lines.append("ошибка получения данных\n")

    # ===== ИТОГО =====
    if total_invested > 0:
        total_profit = total_current - total_invested
        total_pct = total_profit / total_invested * 100
        sign = "+" if total_profit >= 0 else ""

        lines.append("💼 Итого по портфелю")
        lines.append(f"Стоимость: {total_current:,.2f} ₽")
        lines.append(
            f"Результат: {sign}{total_profit:,.2f} ₽ "
            f"({sign}{total_pct:.2f}%)"
        )

    return "\n".join(lines)


def send_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        if not chat_id:
            continue
        requests.post(
            url,
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )


def main():
    send_message(build_message())


if __name__ == "__main__":
    main()

print("CHAT_ID:", os.environ.get("CHAT_ID"))
print("CHAT_ID_WIFE:", os.environ.get("CHAT_ID_WIFE"))
