"""
Модуль для чтения кода подтверждения из любого email-провайдера.

Используется IMAP для подключения к почтовому ящику.
Поддерживает: Gmail, Mail.ru, Yandex, Rambler и другие.

Для Gmail и Yandex нужен App Password (не обычный пароль).
Для Mail.ru и Rambler — обычный пароль от почтового ящика.

Как создать App Password для Gmail:
1. Google Account → Security → 2-Step Verification
2. App Passwords (внизу страницы)
3. Создать пароль для приложения "Mail"

Для Mail.ru:
1. Настройки → Безопасность → Пароли приложений
2. Создать пароль для "Почтовый клиент"
"""

import imaplib
from email.header import decode_header
from email.message import Message as EmailMessage
import logging
import re
import time
from typing import Optional

logger = logging.getLogger(__name__)


def _get_imap_config(email_addr: str) -> tuple:
    """
    Определяет IMAP-сервер по домену email.

    Returns:
        Кортеж (imap_server, port, use_app_password)
    """
    domain = email_addr.split("@")[-1].lower()

    # Gmail
    if domain == "gmail.com":
        return ("imap.gmail.com", 993, True)

    # Mail.ru
    if domain in ("mail.ru", "bk.ru", "inbox.ru"):
        return ("imap.mail.ru", 993, False)

    # Yandex
    if domain == "yandex.ru":
        return ("imap.yandex.ru", 993, True)

    # Rambler
    if domain == "rambler.ru":
        return ("imap.rambler.ru", 993, False)

    # По умолчанию — Gmail
    return ("imap.gmail.com", 993, True)


def get_ozon_confirmation_code(
    max_wait: int = 60,
    check_interval: int = 5,
) -> Optional[str]:
    """
    Подключается к почтовому ящику по IMAP и ищет письмо от Ozon с кодом подтверждения.

    Args:
        max_wait: Максимальное время ожидания письма (сек)
        check_interval: Интервал между проверками (сек)

    Returns:
        Код подтверждения (строка) или None, если письмо не найдено
    """
    import imaplib
    import email
    from email.header import decode_header

    logger.info("Подключение к почтовому ящику IMAP...")

    # Читаем credentials из config
    from config import GMAIL_EMAIL, GMAIL_APP_PASSWORD

    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        logger.error("GMAIL_EMAIL или GMAIL_APP_PASSWORD не заданы в .env")
        return None

    # Определяем IMAP-сервер по домену email
    imap_server, port, use_app_password = _get_imap_config(GMAIL_EMAIL)
    logger.info(
        "IMAP-сервер: %s:%d (домен: %s)",
        imap_server,
        port,
        GMAIL_EMAIL.split("@")[-1],
    )

    start_time = time.time()
    attempt = 0

    while time.time() - start_time < max_wait:
        attempt += 1
        logger.info("Проверка почты (попытка %d)...", attempt)

        mail = None
        try:
            # Подключение к IMAP
            mail = imaplib.IMAP4_SSL(imap_server, port)
            mail.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            logger.info("Успешная авторизация в почтовый ящик")

            # Выбор папки Inbox
            status, _ = mail.select("inbox", readonly=True)
            if status != "OK":
                logger.warning("Не удалось открыть inbox: %s", status)
                time.sleep(check_interval)
                continue

            # Поиск писем от Ozon (используем UID для надёжности)
            logger.info("Поиск писем от Ozon...")
            status, messages = mail.uid('search', None, '(FROM "ozon.ru")')
            if status != "OK":
                logger.error("Ошибка при поиске писем")
                time.sleep(check_interval)
                continue

            email_ids = messages[0].split()
            if not email_ids:
                logger.info("Писем от Ozon не найдено, ждём...")
                time.sleep(check_interval)
                continue

            logger.info("Найдено %d писем от Ozon", len(email_ids))

            # Проверяем последние 3 письма (от нового к старому)
            for email_id in email_ids[-3:][::-1]:
                code = _check_email(mail, email_id)
                if code:
                    logger.info("Код подтверждения найден: %s", code)
                    mail.close()
                    mail.logout()
                    return code

            time.sleep(check_interval)

        except imaplib.IMAP4.error as e:
            logger.error("Ошибка IMAP: %s", e)
            time.sleep(check_interval)
        except Exception as e:
            logger.error("Неожиданная ошибка при чтении почты: %s", e)
            time.sleep(check_interval)
        finally:
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass

    logger.warning(
        "Письмо от Ozon не найдено за %d секунд (%d попыток)",
        max_wait,
        attempt,
    )
    return None


def _check_email(mail: imaplib.IMAP4, email_id: bytes) -> Optional[str]:
    """Проверить одно письмо на наличие кода подтверждения."""
    try:
        status, msg_data = mail.uid('fetch', email_id, "(RFC822)")
        if status != "OK":
            logger.warning("UID fetch failed for %s: %s", email_id, msg_data)
            return None

        raw_email = msg_data[0][1]
        msg = EmailMessage()
        msg.set_payload(raw_email.decode('utf-8', errors='replace'))

        # Декодирование subject
        subject = _decode_mime_header(msg["Subject"])
        logger.debug("Тема письма: %s", subject)

        # Поиск кода в subject
        code = _extract_code_from_text(subject)
        if code:
            logger.info("Код найден в subject: %s", code)
            return code

        # Поиск кода в body
        code = _extract_code_from_text(_get_email_body(msg))
        if code:
            logger.info("Код найден в body: %s", code)
            return code

    except Exception as e:
        logger.debug("Ошибка при обработке письма %s: %s", email_id, e)

    return None


def _decode_mime_header(header_value: str) -> str:
    """Декодирование MIME-заголовка (возможно, закодированного в UTF-8)."""
    if not header_value:
        return ""
    parts = decode_header(header_value)
    decoded_parts = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded_parts.append(part)
    return " ".join(decoded_parts)


def _extract_code_from_text(text: str) -> Optional[str]:
    """Извлечение 4-8 значного кода из текста письма."""
    if not text:
        return None
    # Ищем код из 4-8 цифр (не часть больших чисел)
    match = re.search(r'(?<!\d)(\d{4,8})(?!\d)', text)
    return match.group(1) if match else None


def _get_email_body(msg: EmailMessage) -> str:
    """Извлечение текстового тела из email-сообщения."""
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Пропускаем вложения
            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body += payload.decode(charset, errors="replace")
            elif content_type == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body += payload.decode(charset, errors="replace")
    else:
        content_type = msg.get_content_type()
        if content_type in ("text/plain", "text/html"):
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                body = payload.decode(charset, errors="replace")

    return body
