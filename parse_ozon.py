"""
Основной скрипт для парсинга карточек товаров Ozon.

Загружает cookies из файла, открывает страницы товаров через Playwright
и извлекает структурированные данные, которые сохраняются в CSV.

Использование:
    python parse_ozon.py
    python parse_ozon.py --sku 2359066702,2829800382
    python parse_ozon.py --cookies custom_cookies.json --output custom.csv
"""

import argparse
import csv
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from config import (
    COOKIES_FILE,
    OUTPUT_CSV,
    DEFAULT_SKU_LIST,
    OZON_PRODUCT_URL_TEMPLATE,
    BROWSER_TIMEOUT,
    PAGE_WAIT_TIMEOUT,
    CSV_DELIMITER,
    CSV_ENCODING,
    CSV_FIELDS,
)
from ozon_parser import parse_product_page

logger = logging.getLogger(__name__)


def load_cookies(filepath: str) -> List[Dict[str, Any]]:
    """
    Загрузка cookies из JSON-файла.

    Args:
        filepath: Путь к файлу cookies.json

    Returns:
        Список cookies для передачи в Playwright
    """
    path = Path(filepath)
    if not path.exists():
        logger.error("Файл cookies не найден: %s", filepath)
        logger.error("Сначала запустите: python get_cookies.py")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        logger.info("Cookies загружены из %s (%d штук)", filepath, len(cookies))
        return cookies
    except json.JSONDecodeError as e:
        logger.error("Ошибка парсинга cookies.json: %s", e)
        return []
    except Exception as e:
        logger.error("Ошибка чтения cookies файла: %s", e)
        return []


def parse_single_sku(
    page,
    sku: str,
    browser_timeout: int = BROWSER_TIMEOUT,
) -> Dict[str, Any]:
    """
    Загрузка и парсинг одной карточки товара.

    Args:
        page: Страница Playwright
        sku: Артикул товара
        browser_timeout: Таймаут загрузки страницы (мс)

    Returns:
        Словарь с данными товара или пустой словарь при ошибке
    """
    url = OZON_PRODUCT_URL_TEMPLATE.format(sku=sku)
    logger.info("Загрузка карточки: %s", url)

    result = {"sku": sku}

    try:
        # Установка таймаута и загрузка страницы
        page.set_default_timeout(browser_timeout)
        response = page.goto(url, wait_until="domcontentloaded")

        if response is None:
            logger.warning("Нет ответа от сервера для SKU %s", sku)
            return result

        if response.status == 404:
            logger.warning("Страница не найдена (404) для SKU %s", sku)
            return result

        if response.status != 200:
            logger.warning(
                "HTTP %d для SKU %s, пробуем парсить...",
                response.status,
                sku,
            )

        # Ожидание загрузки контента
        try:
            # Ждём появления заголовка товара или любого контента
            page.wait_for_selector("h1, [data-widget='product-title'], [data-testid='product-title']",
                                   timeout=PAGE_WAIT_TIMEOUT)
        except PlaywrightTimeoutError:
            logger.warning(
                "Не удалось найти заголовок товара для SKU %s, "
                "возможно, страница заблокирована ABT",
                sku,
            )

        # Дополнительная пауза для загрузки JS-данных
        page.wait_for_timeout(3000)

        # Извлечение HTML
        page_html = page.content()

        if not page_html or len(page_html) < 1000:
            logger.warning("HTML страницы слишком короткий для SKU %s (%d символов)",
                           sku, len(page_html) if page_html else 0)
            return result

        # Парсинг
        result = parse_product_page(page_html, sku)

    except PlaywrightTimeoutError:
        logger.error("Таймаут загрузки страницы для SKU %s", sku)
    except Exception as e:
        logger.error("Ошибка парсинга SKU %s: %s", sku, e, exc_info=True)

    return result


def parse_products(
    sku_list: List[str],
    cookies_file: str = COOKIES_FILE,
    output_file: str = OUTPUT_CSV,
) -> List[Dict[str, Any]]:
    """
    Парсинг списка товаров и сохранение результатов в CSV.

    Args:
        sku_list: Список SKU для парсинга
        cookies_file: Путь к файлу cookies
        output_file: Путь к выходному CSV

    Returns:
        Список словарей с данными товаров
    """
    logger.info("=" * 60)
    logger.info("НАЧАЛО ПАРСИНГА ТОВАРОВ")
    logger.info("SKU для парсинга: %s", sku_list)
    logger.info("Cookies файл: %s", cookies_file)
    logger.info("Выходной файл: %s", output_file)
    logger.info("=" * 60)

    # Загрузка cookies
    cookies = load_cookies(cookies_file)
    if not cookies:
        logger.warning(
            "Cookies не загружены. Парсинг будет выполнен без авторизации. "
            "Некоторые данные могут быть недоступны."
        )

    results = []
    success_count = 0
    error_count = 0

    with sync_playwright() as p:
        # Запуск браузера
        logger.info("Запуск браузера Chromium...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # Создание контекста с cookies и реалистичными параметрами
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )

        # Добавляем cookies если есть
        if cookies:
            context.add_cookies(cookies)
            logger.info("Cookies добавлены в контекст")

        page = context.new_page()
        page.set_default_timeout(BROWSER_TIMEOUT)

        try:
            for idx, sku in enumerate(sku_list, 1):
                logger.info(
                    "--- [%d/%d] Парсинг SKU: %s ---",
                    idx,
                    len(sku_list),
                    sku,
                )

                start_time = time.time()

                # Парсинг товара
                product_data = parse_single_sku(page, sku)
                results.append(product_data)

                elapsed = time.time() - start_time

                # Проверка успешности
                has_title = product_data.get("title") is not None
                has_price = product_data.get("price") is not None

                if has_title or has_price:
                    success_count += 1
                    logger.info(
                        "✅ SKU %s успешно распарсен за %.1fs: "
                        "title=%s, price=%.2f",
                        sku,
                        elapsed,
                        product_data.get("title", "N/A")[:40],
                        product_data.get("price", 0),
                    )
                else:
                    error_count += 1
                    logger.warning(
                        "⚠️ SKU %s распарсен без данных за %.1fs",
                        sku,
                        elapsed,
                    )

                # Пауза между запросами (anti-detect)
                if idx < len(sku_list):
                    pause = 2 + hash(sku) % 3  # 2-4 секунды
                    logger.info("Пауза %.0f сек перед следующим запросом...", pause)
                    page.wait_for_timeout(int(pause * 1000))

        finally:
            browser.close()
            logger.info("Браузер закрыт")

    # Сохранение результатов в CSV
    logger.info("=" * 60)
    logger.info("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    logger.info("Всего SKU: %d | Успешно: %d | Ошибки: %d",
                len(sku_list), success_count, error_count)

    _save_to_csv(results, output_file)

    logger.info("=" * 60)
    logger.info("ПАРСИНГ ЗАВЕРШЁН")
    logger.info("=" * 60)

    return results


def _save_to_csv(results: List[Dict[str, Any]], output_file: str) -> None:
    """
    Сохранение результатов парсинга в CSV-файл.
    """
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "w", newline="", encoding=CSV_ENCODING) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=CSV_FIELDS,
                delimiter=CSV_DELIMITER,
            )
            writer.writeheader()

            for product in results:
                # Форматирование булевого поля
                row = {}
                for field in CSV_FIELDS:
                    value = product.get(field)
                    if field == "has_rich_content" and value is not None:
                        row[field] = str(value).lower()  # "true" / "false"
                    elif field == "price" and value is not None:
                        row[field] = round(value, 2)
                    elif field == "rating" and value is not None:
                        row[field] = round(value, 1)
                    elif value is not None:
                        row[field] = str(value)
                    else:
                        row[field] = ""

                writer.writerow(row)

        logger.info("Результаты сохранены в %s (%d записей)", path, len(results))

    except Exception as e:
        logger.error("Ошибка записи CSV: %s", e, exc_info=True)


def main():
    """Точка входа с поддержкой аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Парсер карточек товаров Ozon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python parse_ozon.py
  python parse_ozon.py --sku 2359066702,2829800382
  python parse_ozon.py --cookies my_cookies.json --output products.csv
        """,
    )
    parser.add_argument(
        "--sku",
        type=str,
        default=None,
        help=f"Список SKU через запятую (по умолчанию: {','.join(DEFAULT_SKU_LIST)})",
    )
    parser.add_argument(
        "--cookies",
        type=str,
        default=COOKIES_FILE,
        help=f"Путь к файлу cookies (по умолчанию: {COOKIES_FILE})",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_CSV,
        help=f"Путь к выходному CSV (по умолчанию: {OUTPUT_CSV})",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Включить подробное логирование (DEBUG)",
    )

    args = parser.parse_args()

    # Настройка логирования
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Определение списка SKU
    sku_list = (
        [s.strip() for s in args.sku.split(",") if s.strip()]
        if args.sku
        else DEFAULT_SKU_LIST
    )

    if not sku_list:
        logger.error("Список SKU пуст!")
        return

    # Запуск парсинга
    parse_products(
        sku_list=sku_list,
        cookies_file=args.cookies,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
