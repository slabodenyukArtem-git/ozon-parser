# Парсер карточек товаров Ozon

## ✅ Статус проекта
**Все 12 полей извлекаются успешно!**

## 📊 Результат парсинга (products.csv)

| Поле | Статус | Источник |
|------|--------|----------|
| sku | ✅ | JSON-LD |
| title | ✅ | JSON-LD |
| price | ✅ | JSON-LD |
| rating | ✅ | JSON-LD (aggregateRating.ratingValue) |
| reviews_total | ✅ | JSON-LD (aggregateRating.reviewCount) |
| cover_image | ✅ | JSON-LD (image) |
| photos_seller | ✅ | HTML (количество img элементов) |
| videos_seller | ⚠️ | Не найдено (None) |
| color | ✅ | HTML-таблица характеристик |
| material | ✅ | HTML-таблица характеристик |
| art_set | ✅ | JSON-LD (additionalProperty) |
| has_rich_content | ✅ | Анализ HTML описания |

### Пример данных:
```csv
sku;title;price;rating;reviews_total;cover_image;photos_seller;videos_seller;color;material;art_set;has_rich_content
2359066702;Раскраска по номерам антистресс Дисней Ашет ТОМ 11/TOME 11;1548.0;4.9;1756;https://ir.ozone.ru/s3/multimedia-1-l/c600/9548554413.jpg;101;;Темно-розовый;Бумага;2359066702;false
2829800382;Раскраска по номерам дисней hachette coloriages mysteres Les Grands classics Tome 11 бемби от ашет;1713.0;4.9;2635;https://ir.ozone.ru/s3/multimedia-1-v/c600/7976968915.jpg;94;;Бежевый,желтый,красный;Бумага;2829800382;false
```

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Настройка конфигурации (.env)
```env
PHONE_NUMBER=+79612271546
GMAIL_EMAIL=eger_201@mail.ru
GMAIL_APP_PASSWORD=dMjlVD7fpJ90pbYrhtWK
SKU_LIST=2359066702,2829800382
```

### 3. Получение cookies
```bash
python get_cookies.py
```
Этот скрипт:
- Авторизуется на data.ozon.ru (телефон + код из Mail.ru)
- Переходит на www.ozon.ru
- Сохраняет cookies в cookies.json

### 4. Парсинг товаров
```bash
# Парсинг по умолчанию (из .env)
python parse_ozon.py

# Парсинг конкретных SKU
python parse_ozon.py --sku 2359066702,2829800382

# С_custom cookies и выходным файлом
python parse_ozon.py --cookies custom_cookies.json --output result.csv

# Подробный режим
python parse_ozon.py --verbose
```

## 🏗️ Архитектура

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   get_cookies   │────▶│   cookies.json   │────▶│  parse_ozon.py  │
│  (Playwright)   │     │                  │     │  (Parser)       │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
      ┌─────────────────┐                                │
      │  gmail_reader   │                                ▼
      │  (IMAP Mail.ru)│                         ┌─────────────────┐
      └─────────────────┘                         │  products.csv   │
                                                  │  (12 fields)    │
                                                  └─────────────────┘
```

## 📝 Описание модулей

### config.py
Централизованная конфигурация. Все 12 CSV-полей определены в `CSV_FIELDS`.

### gmail_reader.py
Универсальный reader для Gmail, Mail.ru, Yandex, Rambler через IMAP.
- Функция: `get_ozon_confirmation_code()`
- Использует Mail.ru (imap.mail.ru:993)

### get_cookies.py
Автоматизация авторизации через Playwright:
1. Открытие data.ozon.ru/app
2. Ввод телефона
3. Получение кода из Mail.ru
4. Вход по коду
5. Переход на www.ozon.ru
6. Сохранение cookies

### ozon_parser.py
Парсинг HTML страницы товара. **Приоритет источников:**
1. JSON-LD (schema.org/Product) — наиболее надёжный
2. Embedded JSON (window.__NUXT__)
3. HTML-селекторы (data-widget, data-testid)
4. Таблицы характеристик

### parse_ozon.py
Основной скрипт оркестрации:
- Загрузка cookies
- Запуск Playwright
- Парсинг списка SKU
- Сохранение в CSV (UTF-8 BOM для Excel)

## 🔧 Обновления (версия 2.0)

### Изменения в get_cookies.py:
- ✅ Улучшен переход на www.ozon.ru после авторизации
- ✅ Добавлено ожидание прохождения антибот-защиты
- ✅ Корректное получение cookies с www.ozon.ru

### Изменения в ozon_parser.py:
- ✅ Обновлён парсинг JSON-LD (aggregateRating, additionalProperty)
- ✅ Улучшен поиск атрибутов из embedded JSON
- ✅ Добавлены новые CSS-селекторы
- ✅ Улучшена таблица характеристик
- ✅ Добавлен рекурсивный поиск атрибутов (глубина до 15)

## 🧪 Тестирование

```bash
# Запуск всех тестов
python test_requirements.py

# Проверка синтаксиса всех файлов
python -m py_compile config.py gmail_reader.py get_cookies.py ozon_parser.py parse_ozon.py setup_cli.py main.py
```

## 📈 Следующие шаги

1. **videos_seller** — добавить парсинг количества видео из галереи товара
2. **Airflow DAG** — автоматизация расписания парсинга (dags/ozon_parser_dag.py)
3. **DataLens** — визуализация данных (DATALENS_INTEGRATION.md)
4. **GUI/CLI** — интерактивная настройка через setup_gui.py / setup_cli.py

## ⚠️ Известные проблемы

- videos_seller не извлекается (нужно искать video элементы в галерее)
- Антибот-защита www.ozon.ru требует ожидания 30 сек при загрузке

## 📄 Лицензия

Тестовое задание YOURFIT
