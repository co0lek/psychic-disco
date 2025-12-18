import requests
import os
from datetime import datetime, timezone, timedelta
import time

# ================= НАСТРОЙКИ =================

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MARKET = "shares"

# ⬇⬇⬇ ЗДЕСЬ ВЫ ДОБАВЛЯЕТЕ ИНСТРУМЕНТЫ ⬇⬇⬇
# ticker  — код инструмента
# board   — торговый режим (TQTF, TQIF и т.д.)
# name    — отображаемое имя (произвольное)
INSTRUMENTS = [
    {
        "ticker": "LQDT",
        "board": "TQTF",
        "name": "Денежный рынок",
    },
    {
        "ticker": "RU000A108ZB2",
        "board": "TQIF",
        "name": "2хОФЗ",
    },
]

# ============================================


def build_url(ticker: str, board: str) -> str:
    return (
        "https://iss.moex.com/iss/"
        f"engines/stock/"
        f"markets/{MARKET}/"
        f"boards/{board}/"
        f"securities/{ticker}.json"
        "?iss.meta=off&iss.only=marketdata"
    )


def extract_price_and_change(marketdata: dict):
    columns = marketdata.get("columns", []) or []
    rows = marketdata.get("data", []) or []

    if not rows or not columns:
        return None, None, None

    row = rows[0]
    idx = {c: i for i, c in enumerate(columns)}

    def v(name):
        return row[idx[name]] if name in idx else None

    # ===== ДЕНЕЖНЫЕ ФОНДЫ / БПИФЫ =====
    wap = v("WAPRICE")
    wap_diff = v("WAPTOPREVWAPRICE")
    wap_diff_pct = v("WAPTOPREVWAPRICEPRCNT")

    if wap is not None:
        return (
            float(wap),
            float(wap_diff) if wap_diff is not None else None,
            float(wap_diff_pct) if wap_diff_pct is not None else None,
        )

    # ===== ФОЛБЭК ДЛЯ АКЦИЙ / ETF =====
    price = v("LAST") or v("MARKETPRICE")
    prev = v("PREVPRICE") or v("LCLOSEPRICE")

    if price is not None and prev not in (None, 0):
        diff_abs = price - prev
        diff_pct = diff_abs / prev * 100
        return float(price), float(diff_abs), float(diff_pct)

    return None, None, None


def get_price(ticker: str, board: str):
    url = build_url(ticker, board)
    print("REQUEST:", url)

    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    marketdata = data.get("marketdata", {})
    return extract_price_and_change(marketdata)


def send_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": text,
        },
        timeout=10,
    )


def main():
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk).strftime("%d.%m.%Y %H:%M")

    lines = [f"📊 Цены фондов\n{now}\n"]

    for inst in INSTRUMENTS:
        ticker = inst["ticker"]
        board = inst["board"]
        name = inst.get("name", ticker)

        price, diff_abs, diff_pct = get_price(ticker, board)

        if price is None:
            lines.append(f"{name} ({ticker})\nнет торговых данных\n")
            continue

        text = f"{name} ({ticker})\nЦена: {price:.4f} ₽\n"

        if diff_abs is not None:
            sign = "+" if diff_abs >= 0 else ""
            text += f"Изменение: {sign}{diff_abs:.4f} ₽"
            if diff_pct is not None:
                text += f" ({sign}{diff_pct:.2f}%)"
            text += "\n"
        else:
            text += "Изменение: нет данных\n"

        lines.append(text)
        time.sleep(0.3)

    send_message("\n".join(lines))


if __name__ == "__main__":
    main()
