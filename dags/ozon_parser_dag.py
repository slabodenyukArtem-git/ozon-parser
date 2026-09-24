"""
Airflow DAG для ежедневного парсинга карточек товаров Ozon.

Установка Airflow (базовая):
    pip install apache-airflow
    airflow db init
    airflow users create --username admin --password admin --firstname Admin --lastname Admin --role Admin --email admin@example.com
    airflow webserver --port 8080
    airflow scheduler

Запуск DAG:
    1. Развернуть DAG-файл в dags/ директории Airflow
    2. Включить DAG в UI (toggle On/Off)
    3. DAG будет запускаться ежедневно по расписанию

Требования:
    - Установленные зависимости из requirements.txt
    - Файл .env с credentials (должен быть доступен на узле Airflow)
    - Playwright browser: playwright install chromium
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Пути (адаптировать под окружение Airflow)
BASE_DIR = Path(__file__).parent.parent.resolve()
ENV_FILE = BASE_DIR / ".env"
COOKIES_FILE = BASE_DIR / "cookies.json"
OUTPUT_CSV = BASE_DIR / "products.csv"

# Загрузка SKU из переменных окружения или config
DEFAULT_SKU_LIST = os.getenv(
    "SKU_LIST",
    "2359066702,2829800382",
).split(",")


def _run_get_cookies(**kwargs):
    """Запуск получения cookies."""
    logging.info("Запуск get_cookies.py...")

    # Устанавливаем .env если существует
    if ENV_FILE.exists():
        os.environ.update(
            dict(line.strip().split("=", 1) for line in ENV_FILE.read_text().splitlines()
                 if line.strip() and not line.startswith("#") and "=" in line)
        )

    # Импортируем и запускаем
    import sys
    sys.path.insert(0, str(BASE_DIR))

    from get_cookies import get_cookies

    success = get_cookies()
    if not success:
        raise RuntimeError("Не удалось получить cookies")

    logging.info("Cookies успешно получены")


def _run_parse_products(**kwargs):
    """Запуск парсинга продуктов."""
    logging.info("Запуск parse_ozon.py...")

    # Устанавливаем .env если существует
    if ENV_FILE.exists():
        os.environ.update(
            dict(line.strip().split("=", 1) for line in ENV_FILE.read_text().splitlines()
                 if line.strip() and not line.startswith("#") and "=" in line)
        )

    import sys
    sys.path.insert(0, str(BASE_DIR))

    from parse_ozon import parse_products

    sku_list = [s.strip() for s in DEFAULT_SKU_LIST if s.strip()]
    results = parse_products(sku_list=sku_list)

    logging.info("Парсинг завершён: %d записей", len(results))

    # Возвращаем результат для передачи в следующие задачи
    kwargs["ti"].xcom_push(key="product_count", value=len(results))
    kwargs["ti"].xcom_push(key="output_file", value=str(OUTPUT_CSV))

    return results


def _export_to_datalens(**kwargs):
    """
    Экспорт данных для DataLens.

    Варианты:
    1. Загрузка CSV в Yandex Object Storage (S3-совместимый)
    2. Запись в ClickHouse/Postgres через SQL
    3. Отправка в Yandex Data Vision

    Ниже — пример для загрузки в Yandex Object Storage.
    """
    logging.info("Экспорт данных для DataLens...")

    ti = kwargs["ti"]
    output_file = ti.xcom_pull(task_ids="parse_products", key="output_file")

    if not output_file or not Path(output_file).exists():
        logging.warning("CSV файл не найден, пропускаем экспорт")
        return

    # Вариант 1: Загрузка в Yandex Object Storage
    # yc storage cp products.csv s3://your-bucket/ozon/products_$(date +%Y%m%d).csv

    # Вариант 2: Запись в ClickHouse
    try:
        import clickhouse_connect
        client = clickhouse_connect.get_client(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
            username=os.getenv("CLICKHOUSE_USER", "default"),
            password=os.getenv("CLICKHOUSE_PASSWORD", ""),
            database=os.getenv("CLICKHOUSE_DB", "ozon_analysis"),
        )

        # Чтение CSV и вставка в ClickHouse
        import csv
        with open(output_file, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = list(reader)

        if rows:
            # Маппинг полей CSV -> ClickHouse
            insert_fields = [
                "sku", "title", "price", "rating", "reviews_total",
                "cover_image", "photos_seller", "videos_seller",
                "color", "material", "art_set", "has_rich_content",
            ]
            client.insert(
                table="ozon_products",
                columns=insert_fields,
                data=[[row.get(f, "") for f in insert_fields] for row in rows],
            )
            logging.info("Записано %d строк в ClickHouse", len(rows))
        else:
            logging.warning("CSV файл пуст")

    except ImportError:
        logging.info("clickhouse-connect не установлен, пропускаем запись в ClickHouse")
    except Exception as e:
        logging.warning("Ошибка записи в ClickHouse: %s", e)

    logging.info("Экспорт завершён")


# --- Определение DAG ---
default_args = {
    "owner": "yourfit",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "max_active_runs": 1,
    "schedule_interval": "0 6 * * *",  # Ежедневно в 06:00 MS
}

with DAG(
    dag_id="ozon_product_parser",
    default_args=default_args,
    description="Ежедневный парсинг карточек товаров Ozon",
    doc_md="""
    ## DAG: ozon_product_parser

    ### Описание:
    Ежедневно собирает данные о товарах с маркетплейса Ozon.

    ### Пайплайн:
    1. **get_cookies** — авторизация на data.ozon.ru, получение cookies
    2. **parse_products** — парсинг карточек товаров, сохранение в CSV
    3. **export_datalens** — экспорт данных в ClickHouse / Object Storage

    ### Переменные окружения:
    - `PHONE_NUMBER` — номер для входа
    - `GMAIL_EMAIL` — email для кода подтверждения
    - `GMAIL_APP_PASSWORD` — App Password от Gmail
    - `SKU_LIST` — список SKU через запятую
    """,
    schedule_interval="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ozon", "parser", "etl"],
) as dag:

    # Task 1: Получение cookies
    get_cookies_task = PythonOperator(
        task_id="get_cookies",
        python_callable=_run_get_cookies,
        provide_context=True,
    )

    # Task 2: Парсинг продуктов
    parse_products_task = PythonOperator(
        task_id="parse_products",
        python_callable=_run_parse_products,
        provide_context=True,
    )

    # Task 3: Экспорт в DataLens / ClickHouse
    export_task = PythonOperator(
        task_id="export_datalens",
        python_callable=_export_to_datalens,
        provide_context=True,
    )

    # Последовательный пайплайн
    get_cookies_task >> parse_products_task >> export_task
