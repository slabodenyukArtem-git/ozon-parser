# DataLens Integration Guide

## Вариант 1: Прямая загрузка CSV

1. **Подготовка данных:**
   ```bash
   # CSV уже создан парсером: products.csv
   # Формат: sku;title;price;rating;... (разделитель ;)
   ```

2. **Загрузка в Yandex Object Storage:**
   ```bash
   yc storage cp products.csv s3://your-bucket/ozon/products_$(date +%Y%m%d).csv
   ```

3. **Подключение в DataLens:**
   - DataLens → Источники данных → Создать
   - Выбрать "Yandex Object Storage"
   - Указать bucket и путь к файлу
   - DataLens автоматически определит структуру

4. **Построение дашборда:**
   - Создать дашборд
   - Добавить визуализации:
     - Таблица: SKU, Title, Price, Rating, Reviews
     - График: динамика цен
     - Фильтры: по цвету, материалу
     - KPI: средний рейтинг, кол-во товаров

## Вариант 2: Через ClickHouse (рекомендуется)

1. **Создание таблицы в ClickHouse:**
   ```sql
   CREATE TABLE ozon_products (
       sku String,
       title String,
       price Float64,
       rating Float64,
       reviews_total UInt32,
       cover_image String,
       photos_seller UInt32,
       videos_seller UInt32,
       color String,
       material String,
       art_set String,
       has_rich_content UInt8,
       parsed_at DateTime DEFAULT now()
   ) ENGINE = MergeTree()
   ORDER BY sku
   PARTITION BY toYYYYMM(parsed_at);
   ```

2. **Загрузка данных:**
   - DAG автоматически загружает CSV в ClickHouse
   - Или вручную:
   ```bash
   clickhouse-client --query="
       INSERT INTO ozon_products
       FORMAT CSVWithNames
   " < products.csv
   ```

3. **Подключение DataLens к ClickHouse:**
   - DataLens → Источники данных → ClickHouse
   - Указать host, port, database
   - Выбрать таблицу `ozon_products`

4. **Дашборд:**
   - **Таблица товаров:** SKU, Title, Price, Rating, Reviews
   - **Средняя цена по категориям:** bar chart
   - **Рейтинг vs Количество отзывов:** scatter plot
   - **Rich content coverage:** pie chart (has_rich_content)
   - **Топ товаров по отзывам:** top-N table

## Вариант 3: Через PostgreSQL

1. **Создание таблицы:**
   ```sql
   CREATE TABLE ozon_products (
       sku VARCHAR(50) PRIMARY KEY,
       title TEXT,
       price DECIMAL(12,2),
       rating DECIMAL(3,1),
       reviews_total INTEGER,
       cover_image TEXT,
       photos_seller INTEGER,
       videos_seller INTEGER,
       color VARCHAR(100),
       material VARCHAR(200),
       art_set VARCHAR(100),
       has_rich_content BOOLEAN,
       parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. **Импорт CSV:**
   ```sql
   COPY ozon_products FROM '/path/to/products.csv'
   WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8');
   ```

3. **Подключение DataLens к PostgreSQL:**
   - DataLens → Источники данных → PostgreSQL
   - Указать connection string
   - Выбрать таблицу

## Примеры визуализаций для дашборда

### KPI-карточки:
- Всего товаров
- Средняя цена
- Средний рейтинг
- % товаров с rich content

### Таблицы:
- Все товары с фильтрами
- Топ-10 по рейтингу
- Топ-10 по количеству отзывов

### Графики:
- Распределение цен (histogram)
- Рейтинг vs Количество отзывов (scatter)
- Наличие rich content (pie)
- Динамика цен (line, при ежедневных запусках)
