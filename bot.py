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

CHAT_IDS = []

print("CHAT_ID:", os.environ.get("CHAT_ID"))
print("CHAT_ID_WIFE:", os.environ.get("CHAT_ID_WIFE"))
