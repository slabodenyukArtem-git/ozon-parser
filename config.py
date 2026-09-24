"""
Конфигурация парсера Ozon.

Чувствительные данные (phone, gmail credentials) читаются из .env файла.
Список SKU можно переопределить при вызове скриптов напрямую.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# --- Пути ---
BASE_DIR = Path(__file__).parent.resolve()
COOKIES_FILE = str(BASE_DIR / "cookies.json")
OUTPUT_CSV = str(BASE_DIR / "products.csv")

# --- Авторизация ---
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "+79991234567")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL", "your@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# --- URL ---
DATA_OZON_URL = "https://data.ozon.ru/"
OZON_PRODUCT_URL_TEMPLATE = "https://www.ozon.ru/product/{sku}/"

# --- Список SKU по умолчанию (можно переопределить в parse_ozon.py) ---
DEFAULT_SKU_LIST = [
    sku.strip()
    for sku in os.getenv("SKU_LIST", "2359066702,2829800382").split(",")
    if sku.strip()
]

# --- Настройки Playwright ---
BROWSER_TIMEOUT = 60000  # мс
PAGE_WAIT_TIMEOUT = 30000  # мс

# --- Настройки Gmail ---
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
GMAIL_CHECK_INTERVAL = 5  # секунд между проверками
GMAIL_MAX_WAIT = 60  # макс. время ожидания письма в секундах

# --- Настройки парсинга ---
PARSE_TIMEOUT = 30  # секунд на одну карточку
CSV_DELIMITER = ";"
CSV_ENCODING = "utf-8-sig"  # BOM для корректного открытия в Excel

# --- Поля для экспорта ---
CSV_FIELDS = [
    "sku",
    "title",
    "price",
    "rating",
    "reviews_total",
    "cover_image",
    "photos_seller",
    "videos_seller",
    "color",
    "material",
    "art_set",
    "has_rich_content",
]
