"""
Точка входа для запуска модулей парсера Ozon.

Использование:
    python main.py setup        — терминальный мастер настройки
    python main.py setup-gui    — GUI-окно для настройки (требует tkinter)
    python main.py cookies      — получить cookies
    python main.py parse        — распарсить товары
    python main.py all          — получить cookies + распарсить
    python main.py parse --sku 2359066702,2829800382

Если .env не найден — автоматически запускается setup.
Если .env найден — сразу показывается справка с командами.
"""

import sys
import logging
from pathlib import Path

from config import DEFAULT_SKU_LIST


def setup_logging(verbose: bool = False):
    """Настройка логирования."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _check_env() -> bool:
    """Проверяет наличие .env файла."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("\n⚠️  Файл .env не найден!")
        print("Создайте его вручную или запустите настройку:\n")
        print("  python main.py setup        — интерактивная настройка")
        print("  python main.py setup-gui    — GUI-окно (Windows, требует tkinter)\n")
        print("Или скопируйте .env.example → .env и заполните данные.\n")
        return False
    return True


def run_get_cookies():
    """Запуск получения cookies."""
    from get_cookies import get_cookies

    setup_logging()
    logger = logging.getLogger(__name__)

    if not _check_env():
        print("Сначала настройте .env файл.")
        return False

    success = get_cookies()
    if success:
        print("\n✅ Cookies успешно получены!")
        print("Теперь запустите: python main.py parse")
    else:
        print("\n❌ Ошибка при получении cookies. Проверьте логи.")
    return success


def run_parse(sku_list=None):
    """Запуск парсинга товаров."""
    from parse_ozon import parse_products

    setup_logging()
    logger = logging.getLogger(__name__)

    if not _check_env():
        print("Сначала настройте .env файл.")
        return None

    skus = sku_list or DEFAULT_SKU_LIST
    logger.info("Запуск парсинга для SKU: %s", skus)

    results = parse_products(sku_list=skus)
    print(f"\n✅ Парсинг завершён! Обработано {len(results)} товаров.")
    print(f"Результаты сохранены в products.csv")
    return results


def run_all(sku_list=None):
    """Полный пайплайн: cookies + парсинг."""
    setup_logging()
    logger = logging.getLogger(__name__)

    if not _check_env():
        print("Сначала настройте .env файл.")
        return False

    logger.info("=" * 60)
    logger.info("ПОЛНЫЙ ПАЙПЛАЙН: ПОЛУЧЕНИЕ COOKIES + ПАРСИНГ")
    logger.info("=" * 60)

    # Шаг 1: Получение cookies
    if not run_get_cookies():
        logger.error("Не удалось получить cookies. Прерывание.")
        return False

    print("\n" + "=" * 60)

    # Шаг 2: Парсинг
    return run_parse(sku_list)


def show_help():
    """Показывает справку по командам."""
    print("\n" + "=" * 60)
    print("  Ozon Parser — Справка")
    print("=" * 60)
    print("\n  Команды:")
    print("  python main.py setup        — настроить .env (телефон, gmail, SKU)")
    print("  python main.py setup-gui    — GUI-окно для настройки (Windows)")
    print("  python main.py cookies      — получить cookies для авторизации")
    print("  python main.py parse        — распарсить товары по SKU из .env")
    print("  python main.py parse --sku 123,456  — распарсить конкретные SKU")
    print("  python main.py all          — получить cookies + распарсить товары")
    print("\n  После настройки:")
    print("  1. python main.py cookies   — получить cookies")
    print("  2. python main.py parse     — распарсить товары")
    print("\n  Файлы:")
    print("  .env              — настройки (email, phone, password, SKU)")
    print("  cookies.json      — cookies для авторизации (создаётся автоматически)")
    print("  products.csv      — результат парсинга")
    print("=" * 60 + "\n")


def main():
    """Основная функция с роутингом команд."""
    if len(sys.argv) < 2:
        # Без аргументов — показываем справку
        show_help()
        return

    command = sys.argv[1].lower()

    if command == "setup":
        # Передаём все аргументы после "setup" в setup_cli
        from setup_cli import main as run_setup_cli
        # sys.argv[2:] — всё что после "setup"
        import sys as _sys
        _sys.argv = [_sys.argv[0]] + _sys.argv[2:]
        run_setup_cli()
    elif command == "setup-gui":
        from setup_gui import main as run_setup_gui
        run_setup_gui()
    elif command == "cookies":
        run_get_cookies()
    elif command == "parse":
        # Поддержка аргументов для parse
        sku_arg = None
        if "--sku" in sys.argv:
            idx = sys.argv.index("--sku")
            if idx + 1 < len(sys.argv):
                sku_arg = sys.argv[idx + 1]
        run_parse(sku_list=sku_arg)
    elif command == "all":
        run_all()
    elif command in ("--help", "-h", "help"):
        show_help()
    else:
        print(f"Неизвестная команда: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
