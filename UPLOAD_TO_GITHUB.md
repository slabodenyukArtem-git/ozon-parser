# 📤 Инструкция по загрузке на GitHub

## Шаг 1: Создайте репозиторий на GitHub

1. Перейдите на https://github.com/new
2. Введите имя репозитория: `ozon-parser`
3. Выберите **Private** или **Public**
4. **НЕ** создавайте README, .gitignore, license (мы уже имеем эти файлы)
5. Нажмите "Create repository"

## Шаг 2: Получите токен для доступа

### Вариант A: GitHub Personal Access Token
1. Перейдите на https://github.com/settings/tokens
2. Нажмите "Generate new token (classic)"
3. Поставьте галочку `repo`
4. Нажмите "Generate token"
5. Скопируйте токен (начинается с `ghp_...`)

### Вариант B: Используйте GitHub Desktop
Если установлен GitHub Desktop, можно загрузить без токена.

## Шаг 3: Загрузите код

### Если есть токен:

```bash
# В папке проекта выполните:
git remote add origin https://github.com/СЛОЖИ_ИМЯ_РЕПОЗИТОРИЯ/ozon-parser.git
git branch -M main
git push -u origin main
```

### С аутентификацией:
```bash
git remote add origin https://github.com/ВАШ_USERNAME/ozon-parser.git
git branch -M main
git push -u origin main
# Введите логин и токен при запросе
```

## Шаг 4: Проверьте

Перейдите на https://github.com/ВАШ_USERNAME/ozon-parser и убедитесь что файлы загружены.

---

## 📁 Что в репозитории:

### Основные файлы:
- ✅ `config.py` - конфигурация
- ✅ `gmail_reader.py` - IMAP reader (Mail.ru)
- ✅ `get_cookies.py` - авторизация Playwright
- ✅ `ozon_parser.py` - парсинг 12 полей
- ✅ `parse_ozon.py` - оркестрация → CSV
- ✅ `setup_gui.py` - GUI (tkinter)
- ✅ `setup_cli.py` - CLI мастер
- ✅ `main.py` - точка входа

### Бонус:
- ✅ `dags/ozon_parser_dag.py` - Airflow DAG
- ✅ `DATALENS_INTEGRATION.md` - интеграция с DataLens

### Документация:
- ✅ `README.md` - быстрый старт
- ✅ `TZ_EVALUATION.md` - оценка ТЗ
- ✅ `IMPLEMENTATION_SUMMARY.md` - детали реализации

### Конфигурация:
- ✅ `.env.example` - пример конфигурации
- ✅ `.gitignore` - защита паролей
- ✅ `requirements.txt` - зависимости
- ✅ `test_requirements.py` - тесты

### Удалено:
- ❌ debug-файлы
- ❌ cookies.json
- ❌ HTML-файлы отладки
- ❌ __pycache__
- ❌ Пароли и чувствительные данные
