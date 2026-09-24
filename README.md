# 🎯 Ozon Product Parser

Парсер карточек товаров Ozon с авторизацией через email и извлечением 12 полей данных.

## 📊 Возможности

- ✅ **Авторизация** — автоматический вход на data.ozon.ru (телефон + код из Mail.ru)
- ✅ **12 полей** — sku, title, price, rating, reviews_total, cover_image, photos_seller, videos_seller, color, material, art_set, has_rich_content
- ✅ **CSV экспорт** — UTF-8 BOM, совместим с Excel
- ✅ **GUI/CLI** — графический и терминальный интерфейсы настройки
- ✅ **Airflow DAG** — ежедневная автоматизация
- ✅ **DataLens** — интеграция с Yandex DataLens

## 🚀 Быстрый старт

### 1. Установка
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Настройка (.env)
```env
PHONE_NUMBER=+79612271546
GMAIL_EMAIL=eger_201@mail.ru
GMAIL_APP_PASSWORD=dMjlVD7fpJ90pbYrhtWK
SKU_LIST=2359066702,2829800382
```

### 3. Запуск
```bash
# GUI настройка
python main.py setup-gui

# Получение cookies
python main.py cookies

# Парсинг товаров
python main.py parse

# Полный цикл
python main.py all
```

## 📁 Структура проекта

```
├── config.py              # Конфигурация
├── gmail_reader.py        # IMAP reader (Mail.ru/Gmail/Yandex)
├── get_cookies.py         # Playwright авторизация
├── ozon_parser.py         # Парсинг HTML → JSON
├── parse_ozon.py          # Оркестрация → CSV
├── setup_gui.py           # GUI (tkinter)
├── setup_cli.py           # CLI мастер
├── main.py                # Точка входа
├── test_requirements.py   # Тесты ТЗ
├── dags/                  # Airflow DAG
├── requirements.txt       # Зависимости
├── .env                   # Конфигурация
└── products.csv           # Результат парсинга
```

## 📊 Результат парсинга

| Поле | Источник | Пример |
|------|----------|--------|
| sku | JSON-LD | 2359066702 |
| title | JSON-LD | Раскраска по номерам... |
| price | JSON-LD | 1548.0 |
| rating | JSON-LD | 4.9 |
| reviews_total | JSON-LD | 1756 |
| cover_image | JSON-LD | https://ir.ozone.ru/... |
| photos_seller | HTML | 101 |
| videos_seller | HTML | - |
| color | HTML specs | Темно-розовый |
| material | HTML specs | Бумага |
| art_set | JSON-LD | 2359066702 |
| has_rich_content | Анализ | false |

## 🧪 Тестирование

```bash
python test_requirements.py
```

**Результат:** 8/8 тестов пройдены ✅



## ⚙️ Требования

- Python 3.10+
- Playwright Chromium
- Mail.ru аккаунт с App Password

## 📝 Лицензия

Тестовое задание YOURFIT
