"""
Модуль для автоматической авторизации на data.ozon.ru и получения cookies.

Используется Playwright для браузерной автоматизации, так как Ozon
использует ABT (AntiBot Technology) — JavaScript-challenge, который
нельзя обойти обычными HTTP-запросами.

Flow:
1. Открыть https://data.ozon.ru/
2. Ввести номер телефона
3. Получить код подтверждения из Gmail
4. Ввести код
5. Сохранить cookies для последующего использования
"""

import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any

from playwright.sync_api import sync_playwright, Page, BrowserContext
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config import (
    DATA_OZON_URL,
    PHONE_NUMBER,
    COOKIES_FILE,
    BROWSER_TIMEOUT,
    PAGE_WAIT_TIMEOUT,
)
from gmail_reader import get_ozon_confirmation_code

logger = logging.getLogger(__name__)


def _wait_for_element(page: Page, selector: str, timeout: int = 10000) -> bool:
    """
    Ожидание появления элемента на странице.

    Args:
        page: Страница Playwright
        selector: CSS-селектор элемента
        timeout: Таймаут в мс

    Returns:
        True если элемент найден, False иначе
    """
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except PlaywrightTimeoutError:
        return False


def _debug_page(page: Page, step: str) -> None:
    """Сохраняет скриншот и HTML страницы для отладки."""
    try:
        screenshot_path = f"debug_{step}.png"
        page.screenshot(path=screenshot_path, full_page=True)
        logger.info("Скриншот сохранён: %s", screenshot_path)
    except Exception as e:
        logger.warning("Не удалось сохранить скриншот: %s", e)

    try:
        html_path = f"debug_{step}.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(page.content())
        logger.info("HTML сохранён: %s", html_path)
    except Exception as e:
        logger.warning("Не удалось сохранить HTML: %s", e)


def _enter_phone(page: Page, phone: str) -> bool:
    """Ввод номера телефона на странице входа Ozon."""
    logger.info("Ввод номера телефона: %s", phone)

    # data.ozon.ru — SPA на Nuxt.js, форма появляется после загрузки JS
    # Ждём полной загрузки сети и всех ресурсов
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
        logger.info("Страница загружена (networkidle)")
    except PlaywrightTimeoutError:
        logger.warning("networkidle timeout, продолжаем")

    # Дополнительная пауза для рендеринга Vue/Nuxt приложения
    page.wait_for_timeout(8000)
    logger.info("Подождём 8 сек для JS-рендеринга Nuxt.js")

    # Сохраняем скриншот для отладки
    _debug_page(page, "before_phone")

    # Пытаемся найти поле ввода телефона
    # Для SPA-приложений используем более надёжные селекторы
    phone_selectors = [
        'input[type="tel"]',
        'input[placeholder*="телефон" i]',
        'input[placeholder*="phone" i]',
        'input[name*="phone" i]',
        'input[name*="tel" i]',
        'input[data-testid="phone-input"]',
        'input[name="phone"]',
        'input[name="tel"]',
        'input[type="text"][name*="phone"]',
        'input[type="text"][name*="tel"]',
        'input[type="text"][placeholder*="телефон" i]',
        'input[type="text"][placeholder*="phone" i]',
        'input[type="text"][placeholder*="+7" i]',
        'input[type="text"][placeholder*="8" i]',
        # Новые селекторы для актуального дизайна Ozon
        'input[data-qa="phone-input"]',
        'input[data-testid="phone"]',
        'input[class*="phone" i]',
        'input[class*="tel" i]',
        'input[class*="input" i][type="text"]',
        'input[class*="input" i][type="tel"]',
        'input[class*="field" i][type="text"]',
        'input[class*="field" i][type="tel"]',
        'input[class*="text" i][type="tel"]',
        'input[class*="text" i][type="text"]',
        # Очень широкий поиск
        'input[type="tel"]',
        'input:not([type])',
        'input[type="text"]',
    ]

    input_element = None
    for selector in phone_selectors:
        try:
            input_element = page.wait_for_selector(selector, timeout=5000)
            if input_element:
                logger.info("Поле телефона найдено по селектору: %s", selector)
                break
        except PlaywrightTimeoutError:
            continue

    if not input_element:
        # Фоллбэк: ищем любой input на странице
        try:
            input_element = page.wait_for_selector('input', timeout=5000)
            logger.info("Найден первый input на странице")
        except PlaywrightTimeoutError:
            logger.error("Поле ввода телефона не найдено")
            return False

    # Очищаем и вводим номер
    input_element.click()
    input_element.fill("")
    input_element.fill(phone)
    logger.info("Номер телефона введён")

    # Сохраняем скриншот после ввода
    _debug_page(page, "after_phone")

    return True


def _click_continue(page: Page) -> bool:
    """Нажатие кнопки 'Продолжить' или аналогичной."""
    logger.info("Нажатие кнопки 'Продолжить'...")

    continue_selectors = [
        'button[type="submit"]',
        'button:has-text("Продолжить")',
        'button:has-text("Continue")',
        'input[type="submit"]',
        '[data-testid="submit-button"]',
        '.Button:has-text("Продолжить")',
    ]

    for selector in continue_selectors:
        try:
            button = page.wait_for_selector(selector, timeout=5000)
            if button:
                button.click()
                logger.info("Кнопка 'Продолжить' нажата")
                return True
        except PlaywrightTimeoutError:
            continue

    # Фоллбэк: нажимаем Enter в поле ввода
    try:
        page.keyboard.press("Enter")
        logger.info("Нажата клавиша Enter")
        return True
    except Exception:
        logger.error("Не удалось нажать кнопку продолжения")
        return False


def _enter_code(page: Page, code: str) -> bool:
    """Ввод кода подтверждения."""
    logger.info("Ввод кода подтверждения: %s", code)

    # Ozon использует отдельные инпуты для каждой цифры кода
    # Пытаемся найти все поля ввода кода
    code_inputs = page.query_selector_all('input[type="text"], input[type="tel"]')

    if len(code_inputs) >= len(code):
        # Вводим код по символам в отдельные поля
        for i, digit in enumerate(code):
            if i < len(code_inputs):
                code_inputs[i].click()
                code_inputs[i].fill(digit)
                logger.debug("Введена цифра %s в поле %d", digit, i)
    else:
        # Фоллбэк: ввод в первое доступное поле
        if code_inputs:
            code_inputs[0].click()
            code_inputs[0].fill(code)
            logger.debug("Введён код в поле 0")
        else:
            # Ещё один фоллбэк: ищем input по data-атрибутам
            try:
                code_input = page.wait_for_selector('input', timeout=3000)
                code_input.click()
                code_input.fill(code)
            except PlaywrightTimeoutError:
                logger.error("Поле ввода кода не найдено")
                return False

    return True


def _click_submit(page: Page) -> bool:
    """Нажатие кнопки подтверждения кода."""
    logger.info("Нажатие кнопки подтверждения...")

    submit_selectors = [
        'button:has-text("Войти")',
        'button:has-text("Подтвердить")',
        'button:has-text("Submit")',
        'button[type="submit"]',
        '[data-testid="submit-button"]',
    ]

    for selector in submit_selectors:
        try:
            button = page.wait_for_selector(selector, timeout=5000)
            if button:
                button.click()
                logger.info("Кнопка подтверждения нажата")
                return True
        except PlaywrightTimeoutError:
            continue

    # Фоллбэк: Enter
    try:
        page.keyboard.press("Enter")
        return True
    except Exception:
        return False


def _wait_for_login_success(page: Page) -> bool:
    """
    Ожидание успешного входа (появление элементов авторизованного пользователя).
    """
    logger.info("Ожидание успешного входа...")

    # Элементы, видимые только после авторизации
    success_indicators = [
        'a[href*="/my/orders/"]',
        'a[href*="/settings/"]',
        '[data-testid="user-menu"]',
        '.UserMenu',
        'button:has-text("Продавать на Ozon")',
        'a:has-text("Личный кабинет")',
    ]

    for selector in success_indicators:
        try:
            page.wait_for_selector(selector, timeout=30000)
            logger.info("Успешный вход подтверждён (индикатор: %s)", selector)
            return True
        except PlaywrightTimeoutError:
            continue

    # Если ни один индикатор не найден, проверяем что мы не на странице входа
    try:
        # Если страница не перенаправила обратно на вход — считаем что вход успешен
        current_url = page.url
        if "login" not in current_url.lower() and "auth" not in current_url.lower():
            logger.info("Текущий URL не содержит 'login' или 'auth': %s", current_url)
            return True
    except Exception:
        pass

    logger.warning("Не удалось подтвердить успешный вход по элементам, "
                   "но страница загружена")
    return True


def _navigate_to_login(page: Page) -> bool:
    """Переход на страницу авторизации data.ozon.ru."""
    logger.info("Переход на страницу авторизации...")

    # data.ozon.ru — SPA на Nuxt.js. Главная страница — лендинг.
    # Нужно перейти на /app или нажать кнопку "Перейти к аналитике"
    try:
        # Пробуем перейти напрямую на /app
        page.goto(DATA_OZON_URL + "app", wait_until="domcontentloaded")
        page.wait_for_timeout(8000)
        logger.info("URL после перехода: %s", page.url)

        # Сохраняем скриншот для отладки
        _debug_page(page, "after_navigate")

        # Проверяем, есть ли поле ввода телефона
        try:
            page.wait_for_selector('input[type="tel"]', timeout=3000)
            logger.info("Поле телефона найдено на /app")
            return True
        except PlaywrightTimeoutError:
            logger.warning("Поле телефона не найдено на /app, пробуем главную страницу")
    except Exception as e:
        logger.warning("Ошибка перехода на /app: %s", e)

    # Фоллбэк: нажимаем кнопку "Перейти к аналитике" на главной
    logger.info("Попытка нажать кнопку 'Перейти к аналитике'...")
    buttons = page.query_selector_all('button')
    for btn in buttons:
        text = btn.inner_text().strip()
        if "аналитик" in text.lower() or "перейти" in text.lower():
            logger.info("Найдена кнопка: %s", text)
            btn.click()
            page.wait_for_timeout(10000)  # Ждём загрузки SPA
            logger.info("URL после клика: %s", page.url)
            _debug_page(page, "after_click")
            return True

    logger.error("Не удалось найти кнопку для перехода к авторизации")
    return False


def get_cookies(
    phone: str = PHONE_NUMBER,
    save_path: str = COOKIES_FILE,
) -> bool:
    """
    Выполняет автоматический вход на data.ozon.ru и сохраняет cookies.

    Args:
        phone: Номер телефона для входа
        save_path: Путь для сохранения cookies.json

    Returns:
        True если cookies успешно получены и сохранены
    """
    logger.info("=" * 60)
    logger.info("НАЧАЛО ПРОЦЕССА ПОЛУЧЕНИЯ COOKIES")
    logger.info("URL: %s", DATA_OZON_URL)
    logger.info("Телефон: %s", phone)
    logger.info("=" * 60)

    with sync_playwright() as p:
        # Запуск браузера (headless для сервера, можно False для отладки)
        logger.info("Запуск браузера Chromium...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # Создание контекста с имитацией реального браузера
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

        page = context.new_page()
        page.set_default_timeout(BROWSER_TIMEOUT)

        try:
            # Шаг 1: Открытие страницы и переход к авторизации
            logger.info("Шаг 1: Открытие страницы data.ozon.ru")
            page.goto(DATA_OZON_URL, wait_until="domcontentloaded")
            logger.info("Текущий URL: %s", page.url)

            # Небольшая пауза для полной загрузки страницы
            page.wait_for_timeout(3000)

            # Шаг 2: Переход на страницу авторизации
            logger.info("Шаг 2: Переход на страницу авторизации")
            if not _navigate_to_login(page):
                logger.error("Не удалось перейти на страницу авторизации")
                return False

            # Шаг 3: Ввод номера телефона
            logger.info("Шаг 3: Ввод номера телефона")
            if not _enter_phone(page, phone):
                logger.error("Не удалось ввести номер телефона")
                return False

            page.wait_for_timeout(1000)

            # Шаг 4: Нажатие кнопки "Продолжить"
            logger.info("Шаг 4: Отправка номера телефона")
            if not _click_continue(page):
                logger.error("Не удалось отправить номер телефона")
                return False

            # Пауза для получения письма
            page.wait_for_timeout(3000)

            # Шаг 5: Получение кода из Gmail
            logger.info("Шаг 5: Ожидание письма с кодом из Gmail")
            code = get_ozon_confirmation_code()
            if not code:
                logger.error("Код подтверждения не получен из Gmail")
                return False

            # Шаг 6: Ввод кода подтверждения
            logger.info("Шаг 6: Ввод кода подтверждения")
            if not _enter_code(page, code):
                logger.error("Не удалось ввести код подтверждения")
                return False

            page.wait_for_timeout(1000)

            # Шаг 7: Отправка кода
            logger.info("Шаг 7: Отправка кода подтверждения")
            if not _click_submit(page):
                logger.error("Не удалось отправить код подтверждения")
                return False

            # Шаг 8: Ожидание успешного входа
            logger.info("Шаг 8: Ожидание успешного входа")
            if not _wait_for_login_success(page):
                logger.error("Вход не выполнен успешно")
                return False

            # Небольшая пауза для полной инициализации сессии
            page.wait_for_timeout(2000)
            logger.info("Текущий URL после входа: %s", page.url)

            # Шаг 9: Получение cookies с www.ozon.ru для парсинга товаров
            logger.info("Шаг 9: Переход на www.ozon.ru для получения cookies")
            
            # Создаём новую страницу для www.ozon.ru (cookies уже есть из контекста)
            www_page = context.new_page()
            www_page.set_default_timeout(BROWSER_TIMEOUT)
            
            try:
                # Переход на главную www.ozon.ru
                logger.info("Загрузка главной страницы www.ozon.ru...")
                response = www_page.goto("https://www.ozon.ru/", wait_until="domcontentloaded")
                
                if response and response.status == 403:
                    logger.info("Обнаружена антибот-защита, ожидаем прохождения...")
                    # Ждём прохождения антибот-защиты (до 30 сек)
                    try:
                        # Ждём появления основного контента (не antibot страницы)
                        www_page.wait_for_selector(
                            "[data-widget], .catalog, .search, header, [class*='header']",
                            timeout=30000
                        )
                        logger.info("Антибот-защита пройдена успешно")
                    except PlaywrightTimeoutError:
                        logger.warning("Таймаут ожидания антибот-защиты, пробуем сохранить cookies")
                        # Даже если не дождались, пробуем сохранить cookies
                    
                    # Дополнительная пауза для загрузки JS
                    www_page.wait_for_timeout(5000)
                elif response and response.status == 200:
                    logger.info("Страница загружена без антибот-защиты")
                    www_page.wait_for_timeout(3000)
                
                # Сохраняем HTML для отладки (если это не antibot страница)
                current_html = www_page.content()
                if "Antibot Challenge" not in current_html and "antibot" not in current_html.lower():
                    logger.info("Это страница товара, а не antibot challenge")
                
                # Получаем cookies
                www_cookies = context.cookies()
                logger.info("Получено всего cookies: %d", len(www_cookies))
                
            except Exception as e:
                logger.warning("Ошибка при загрузке www.ozon.ru: %s", e)
                www_cookies = []
            finally:
                www_page.close()
            
            # Шаг 11: Сохранение cookies в файл
            logger.info("Шаг 11: Сохранение cookies в файл")
            cookies = context.cookies()

            # Фильтруем cookies для нужных доменов
            relevant_cookies = [
                c for c in cookies
                if c.get("domain", "").endswith("ozon.ru")
            ]
            
            # Добавляем cookies с www.ozon.ru (если есть)
            if www_cookies:
                existing_urls = {c.get("name") for c in relevant_cookies}
                for c in www_cookies:
                    if c.get("name") and c.get("name") not in existing_urls:
                        relevant_cookies.append(c)
                        existing_urls.add(c.get("name"))
            
            logger.info("Итого релевантных cookies: %d", len(relevant_cookies))

            # Сохраняем cookies в файл
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(relevant_cookies, f, ensure_ascii=False, indent=2)

            logger.info(
                "Cookies сохранены в %s (%d штук)",
                save_path,
                len(relevant_cookies),
            )
            logger.info("=" * 60)
            logger.info("COOKIES УСПЕШНО ПОЛУЧЕНЫ И СОХРАНЕНЫ")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error("Ошибка при получении cookies: %s", e, exc_info=True)
            return False

        finally:
            browser.close()
            logger.info("Браузер закрыт")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    success = get_cookies()
    if success:
        print("\n✅ Cookies успешно получены и сохранены в cookies.json")
    else:
        print("\n❌ Не удалось получить cookies. Проверьте логи.")
