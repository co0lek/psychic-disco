import requests
import os
from datetime import datetime, timezone, timedelta
import time
import traceback

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MARKET = "shares"
BOARD = "TQTF"

# ЯВНО УКАЖИТЕ ТУТ СВОИ ТИКЕРЫ (скобки/строки)
TICKERS = [
    "LQDT",
    # "WIM2OFZ",
    # "SBGB",
]

# Таймауты
REQUEST_TIMEOUT = 10
SLEEP_BETWEEN = 0.25  # чтобы не нагружать API

# =======================================

def build_url(ticker: str) -> str:
    return (
        "https://iss.moex.com/iss/"
        f"engines/stock/"
        f"markets/{MARKET}/"
        f"boards/{BOARD}/"
        f"securities/{ticker}.json"
        "?iss.meta=off&iss.only=marketdata"
    )

def fetch_marketdata_json(url: str):
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("HTTP error:", e)
        return None

def extract_price_and_prev_from_marketdata(md: dict):
    """
    Возвращает tuple (price, prev_price, info)
    price и prev_price — float или None
    info — словарь с тем, какие поля были найдены (для отладки)
    """
    columns = md.get("columns", []) or []
    rows = md.get("data", []) or []
    info = {"columns": columns}

    if not rows or not columns:
        info["rows_present"] = False
        return None, None, info

    info["rows_present"] = True
    row = rows[0]
    col_index = {c: i for i, c in enumerate(columns)}

    def val(name):
        if name in col_index:
            v = row[col_index[name]]
            return v
        return None

    # Список кандидатов на текущую цену (порядок важен)
    price_candidates = [
        "MARKETPRICE", "LAST", "LCURRENTPRICE", "WAPRICE",
        "CLOSEPRICE", "MARKETPRICE2", "MARKETPRICETODAY"
    ]

    # Список кандидатов на предыдущую цену (опорную)
    prev_candidates = [
        "PREVPRICE", "LCLOSEPRICE", "CLOSEPRICE", "MARKETPRICETODAY"
    ]

    found_price = None
    for p in price_candidates:
        v = val(p)
        if v is not None:
            found_price = v
            info["price_field"] = p
            break

    found_prev = None
    for p in prev_candidates:
        v = val(p)
        if v is not None:
            found_prev = v
            info["prev_field"] = p
            break

    try:
        price_f = float(found_price) if found_price is not None else None
    except Exception:
        price_f = None

    try:
        prev_f = float(found_prev) if found_prev is not None else None
    except Exception:
        prev_f = None

    return price_f, prev_f, info

def get_price(ticker: str):
    url = build_url(ticker)
    print("REQUEST URL:", url)
    data = fetch_marketdata_json(url)
    if data is None:
        return None, None, {"error": "http_failed", "url": url}

    marketdata = data.get("marketdata", {})
    price, prev, info = extract_price_and_prev_from_marketdata(marketdata)
    info["url"] = url
    return price, prev, info

def send_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print("Telegram send failed:", r.status_code, r.text)
    except Exception as e:
        print("Telegram exception:", e)

def build_message():
    msk = timezone(timedelta(hours=3))
    now = datetime.now(msk).strftime("%d.%m.%Y %H:%M")
    lines = [f"📊 Цены фондов\n{now}\n"]

    for ticker in TICKERS:
        try:
            price, prev, info = get_price(ticker)
        except Exception:
            price = prev = None
            info = {"error": "exception", "trace": traceback.format_exc()}

        if price is None and prev is None:
            lines.append(f"{ticker}\nнет торговых данных\n")
            # Для дебага: можно добавить ссылку/поля (закомментируйте, если не нужно)
            # lines.append(f"Источник: {info.get('url')}\nПоля: {info.get('columns')}\n")
            time.sleep(SLEEP_BETWEEN)
            continue

        # Если есть цена, но нет prev — всё равно показываем цену и отмечаем отсутствие базы
        if price is not None and prev is None:
            lines.append(
                f"{ticker}\n"
                f"Цена: {price:.4f} ₽\n"
                f"Изменение за день: нет данных для базовой цены\n"
            )
            time.sleep(SLEEP_BETWEEN)
            continue

        # Если оба есть — считаем изменение
        if price is not None and prev is not None:
            try:
                change = (price - prev) / prev * 100 if prev != 0 else None
            except Exception:
                change = None

            sign = "+" if (change is not None and change >= 0) else ""
            change_str = f"{sign}{change:.2f}%" if change is not None else "n/a"

            lines.append(
                f"{ticker}\n"
                f"Цена: {price:.4f} ₽\n"
                f"Изменение за день: {change_str}\n"
            )

        time.sleep(SLEEP_BETWEEN)

    return "\n".join(lines)

def main():
    try:
        text = build_message()
        send_message(text)
    except Exception as e:
        # на случай непредвиденной ошибки — отправляем стектрейс в телеграм для отладки
        err = f"Bot exception:\n{e}\n{traceback.format_exc()}"
        print(err)
        try:
            send_message("Ошибка в боте. Смотрите лог Actions.")
        except:
            pass

if __name__ == "__main__":
    main()
