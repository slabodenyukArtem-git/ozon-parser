"""
Модуль для парсинга карточки товара с Ozon.

Извлекает 12 полей из HTML-страницы товара:
sku, title, price, rating, reviews_total, cover_image,
photos_seller, videos_seller, color, material, art_set, has_rich_content.

Данные извлекаются из:
1. JSON-LD блоков (<script type="application/ld+json">)
2. Встроенных JSON-объектов (window.__NUXT__, script[type="application/json"])
3. HTML-элементов (BeautifulSoup)
4. Meta-тегов (og:*)
"""

import re
import json
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _parse_price(price_str: str) -> Optional[float]:
    """
    Парсинг цены из строки вида '1 299 ₽' или '1299,00'.
    """
    if not price_str:
        return None
    # Убираем все пробелы и символы валюты
    cleaned = re.sub(r"[^\d.,]", "", price_str)
    # Заменяем запятую на точку для float
    cleaned = cleaned.replace(",", ".")
    # Убираем разделители тысяч (пробелы уже убраны выше)
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_rating(rating_str: str) -> Optional[float]:
    """
    Парсинг рейтинга из строки вида '4.8' или '4,8'.
    """
    if not rating_str:
        return None
    cleaned = rating_str.strip().replace(",", ".")
    try:
        value = float(cleaned)
        return round(value, 1) if 0 < value <= 5 else None
    except ValueError:
        return None


def _parse_int(value_str: str) -> Optional[int]:
    """
    Парсинг целого числа из строки.
    """
    if not value_str:
        return None
    cleaned = re.sub(r"[^\d]", "", value_str)
    try:
        return int(cleaned)
    except ValueError:
        return None


def _extract_json_ld(soup: BeautifulSoup) -> Optional[Dict]:
    """
    Извлечение данных из JSON-LD блоков на странице.
    JSON-LD используется для SEO и содержит структурированные данные о товаре.
    """
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            # JSON-LD может быть объектом или массивом
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
            elif isinstance(data, dict) and data.get("@type") == "Product":
                return data
            # Если это @graph, ищем Product внутри
            if isinstance(data, dict) and "@graph" in data:
                for item in data["@graph"]:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


def _extract_embedded_json(page_html: str) -> Optional[Dict]:
    """
    Извлечение встроенных JSON-объектов из HTML (window.__NUXT__, __INITIAL_STATE__ и т.п.).
    Nuxt.js хранит состояние приложения в window.__NUXT__.
    """
    # Паттерны для поиска встроенных JSON
    patterns = [
        r'window\.__NUXT__\s*=\s*({.*?});?\s*</script>',
        r'window\.__INITIAL_STATE__\s*=\s*({.*?});\s*</script>',
        r'window\.__NEXT_DATA__\s*=\s*({.*?});\s*</script>',
        r'window\.__DATA__\s*=\s*({.*?});\s*</script>',
        r'<script type="application/json" id=".*?">(.*?)</script>',
    ]

    for pattern in patterns:
        match = re.search(pattern, page_html, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    return None


def _get_product_attributes(embedded_data: Optional[Dict]) -> Dict[str, str]:
    """
    Извлечение атрибутов товара (цвет, материал, артикул) из встроенных данных.
    Ищет объекты с ключами: attributes, properties, specs, parameters, characteristics.
    """
    attributes = {}

    if not embedded_data:
        return attributes

    # Рекурсивный поиск атрибутов в JSON-структуре
    def _search_for_attributes(obj, depth=0):
        """Ищем объект с атрибутами товара."""
        if depth > 15 or not obj:
            return {}

        if isinstance(obj, dict):
            # Проверяем, есть ли в словаре ключи с атрибутами
            attr_keys = ["attributes", "properties", "specs", "parameters", "characteristics"]
            for key in attr_keys:
                if key in obj:
                    value = obj[key]
                    # Если это список атрибутов {name: value}
                    if isinstance(value, list):
                        result = {}
                        for item in value:
                            if isinstance(item, dict):
                                name = item.get("name", "") or item.get("propertyName", "")
                                val = item.get("value", "") or item.get("propertyValue", "")
                                if name and val:
                                    result[name.lower()] = str(val)
                        if result:
                            return result
                    # Словарь атрибутов
                    elif isinstance(value, dict):
                        return {
                            k.lower(): str(v)
                            for k, v in value.items()
                            if v
                        }

            # Рекурсивный поиск вложенных структур
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    result = _search_for_attributes(value, depth + 1)
                    if result:
                        return result

        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    result = _search_for_attributes(item, depth + 1)
                    if result:
                        return result

        return {}

    return _search_for_attributes(embedded_data)


def _extract_from_json_ld(json_ld: Optional[Dict], soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Извлечение данных из JSON-LD блока.
    JSON-LD содержит семантические данные по схеме Schema.org/Product.
    """
    result = {}

    if not json_ld:
        return result

    # Название товара
    result["title"] = json_ld.get("name")

    # Цена
    offers = json_ld.get("offers", {})
    if isinstance(offers, dict):
        result["price"] = _parse_price(str(offers.get("price", "")))
    elif isinstance(offers, list):
        for offer in offers:
            if isinstance(offer, dict) and offer.get("price"):
                result["price"] = _parse_price(str(offer["price"]))
                break

    # Рейтинг
    agg_rating = json_ld.get("aggregateRating", {})
    if isinstance(agg_rating, dict):
        result["rating"] = _parse_rating(str(agg_rating.get("ratingValue", "")))
        result["reviews_total"] = _parse_int(str(agg_rating.get("reviewCount", "")))

    # Изображение
    image = json_ld.get("image")
    if isinstance(image, str):
        result["cover_image"] = image
    elif isinstance(image, list) and image:
        result["cover_image"] = image[0] if isinstance(image[0], str) else None

    # Атрибуты из additionalProperty
    additional_props = json_ld.get("additionalProperty", [])
    if isinstance(additional_props, list):
        for prop in additional_props:
            if isinstance(prop, dict):
                prop_name = prop.get("name", "").lower()
                prop_value = prop.get("value", "")
                if prop_name and prop_value:
                    if "цвет" in prop_name or "color" in prop_name or "colour" in prop_name:
                        result["color"] = str(prop_value)
                    elif "material" in prop_name or "материал" in prop_name:
                        result["material"] = str(prop_value)
                    elif "арт" in prop_name or "article" in prop_name:
                        if "art_set" not in result:
                            result["art_set"] = str(prop_value)

    return result


def _extract_from_html(soup: BeautifulSoup, page_html: str) -> Dict[str, Any]:
    """
    Извлечение данных из HTML-элементов страницы.
    Использует CSS-селекторы для нахождения элементов с данными.
    """
    result = {}

    # --- SKU ---
    sku_selectors = [
        '[data-field="sku"]',
        '[data-sku]',
        '[itemprop="sku"]',
        'meta[itemprop="sku"]',
        'meta[name="sku"]',
    ]
    for selector in sku_selectors:
        elem = soup.select_one(selector)
        if elem:
            result["sku"] = elem.get("content") or elem.get_text(strip=True)
            break

    # --- Title ---
    title_selectors = [
        'h1',
        '[data-widget="product-title"]',
        '[data-testid="product-title"]',
        'meta[property="og:title"]',
        'meta[name="title"]',
    ]
    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem:
            result["title"] = elem.get("content") or elem.get_text(strip=True)
            if result["title"]:
                break

    # --- Price ---
    price_selectors = [
        'meta[property="og:price:amount"]',
        'meta[property="product:price:amount"]',
        '[data-widget="price-block"]',
        '[data-testid="price-value"]',
        '.price-main',
        '[class*="price"] [class*="value"]',
        '[class*="price-value"]',
    ]
    for selector in price_selectors:
        elem = soup.select_one(selector)
        if elem:
            price_text = elem.get("content") or elem.get_text(strip=True)
            result["price"] = _parse_price(price_text)
            if result["price"]:
                break

    # --- Rating ---
    rating_selectors = [
        'meta[itemprop="ratingValue"]',
        '[data-widget="rating"]',
        '[data-testid="product-rating"]',
        '[class*="rating"] [class*="value"]',
    ]
    for selector in rating_selectors:
        elem = soup.select_one(selector)
        if elem:
            rating_text = elem.get("content") or elem.get("aria-label") or elem.get_text(strip=True)
            result["rating"] = _parse_rating(rating_text)
            if result["rating"]:
                break

    # --- Reviews count ---
    reviews_selectors = [
        'meta[itemprop="reviewCount"]',
        '[data-widget="reviews-count"]',
        '[data-testid="reviews-count"]',
        '[class*="reviews"] [class*="count"]',
    ]
    for selector in reviews_selectors:
        elem = soup.select_one(selector)
        if elem:
            reviews_text = elem.get("content") or elem.get_text(strip=True)
            result["reviews_total"] = _parse_int(reviews_text)
            if result["reviews_total"]:
                break

    # --- Cover image ---
    image_selectors = [
        'meta[property="og:image"]',
        'meta[itemprop="image"]',
        'meta[name="image"]',
        '[data-widget="product-main-image"]',
    ]
    for selector in image_selectors:
        elem = soup.select_one(selector)
        if elem:
            result["cover_image"] = elem.get("content") or elem.get("src") or elem.get("data-src")
            if result["cover_image"]:
                break

    # Если cover_image не найден через meta, ищем первое изображение
    if not result.get("cover_image"):
        img = soup.find("img", itemprop="image")
        if img:
            result["cover_image"] = img.get("src") or img.get("data-src")

    # --- Photos count ---
    # Ищем количество изображений в галерее
    photos_selectors = [
        '[data-widget="gallery-photos-count"]',
        '[data-testid="gallery-photos-count"]',
        '[class*="gallery"] [class*="photos-count"]',
    ]
    for selector in photos_selectors:
        elem = soup.select_one(selector)
        if elem:
            result["photos_seller"] = _parse_int(elem.get_text(strip=True))
            break

    # Если не нашли по data-widget, ищем через JSON-LD или embedded JSON
    if "photos_seller" not in result:
        # Ищем все изображения товара
        all_images = soup.find_all("img")
        if all_images:
            result["photos_seller"] = len(all_images)

    # --- Videos count ---
    videos_selectors = [
        '[data-widget="gallery-videos-count"]',
        '[data-testid="gallery-videos-count"]',
        '[class*="gallery"] [class*="videos-count"]',
    ]
    for selector in videos_selectors:
        elem = soup.select_one(selector)
        if elem:
            result["videos_seller"] = _parse_int(elem.get_text(strip=True))
            break

    # Если не нашли по data-widget, ищем video элементы
    if "videos_seller" not in result:
        videos = soup.find_all("video")
        if videos:
            result["videos_seller"] = len(videos)

    # --- Description (для проверки rich content) ---
    desc_selectors = [
        '[data-widget="description"]',
        '[data-testid="description"]',
        '[class*="product-description"]',
        '[class*="rich-content"]',
        '[class*="description-block"]',
    ]
    desc_elem = None
    for selector in desc_selectors:
        desc_elem = soup.select_one(selector)
        if desc_elem:
            break

    # Если не нашли по data-widget, ищем по классам
    if not desc_elem:
        desc_classes = ["description", "rich-content", "product-description", "description-block"]
        for cls in desc_classes:
            desc_elem = soup.find(class_=re.compile(r"(?i)({})".format(cls)))
            if desc_elem:
                break

    if desc_elem:
        result["_description_html"] = str(desc_elem)

    return result


def _extract_attributes_from_html(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Извлечение атрибутов товара (цвет, материал, артикул) из HTML-таблиц характеристик.
    Ищет таблицы с классами .specs, .characteristics, [data-widget="product-specs"] и т.п.
    """
    attributes = {}

    # Ищем блок характеристик
    specs_selectors = [
        '[data-widget="product-specs"]',
        '[data-testid="product-specs"]',
        '.specs',
        '.characteristics',
        '.product-characteristics',
        '[class*="specs"]',
        '[class*="characteristics"]',
    ]

    specs_block = None
    for selector in specs_selectors:
        specs_block = soup.select_one(selector)
        if specs_block:
            break

    if not specs_block:
        # Фоллбэк: ищем таблицы с характеристиками
        tables = soup.find_all("table")
        for table in tables:
            caption = table.find(["caption", "th"])
            if caption and any(word in caption.get_text().lower()
                              for word in ["характеристик", "специф", "specs"]):
                specs_block = table
                break

    if not specs_block:
        # Фоллбэк: ищем любые списки с параметрами
        dt_elements = soup.find_all("dt")
        for dt in dt_elements[:20]:  # Ограничиваем для производительности
            dd = dt.find_next_sibling("dd")
            if dd:
                name = dt.get_text(strip=True).lower()
                value = dd.get_text(strip=True)
                if name and value:
                    attributes[name] = value

    if specs_block and not attributes:
        # Парсим строки характеристик
        rows = specs_block.find_all(["tr", "div"], class_=re.compile(r"(?i)(row|item|spec)"))
        if not rows:
            rows = specs_block.find_all(["tr", "li"])

        for row in rows:
            name_elem = row.find(["td", "th", "dt", "span"], class_=re.compile(r"(?i)(name|label)"))
            value_elem = row.find(["td", "th", "dd", "span"], class_=re.compile(r"(?i)(value|data)"))

            if not name_elem:
                name_elem = row.find(["td", "th", "dt"])
            if not value_elem and len(row.find_all(["td", "th", "dd", "div"])) >= 2:
                cells = row.find_all(["td", "th", "dd", "div"])
                value_elem = cells[-1]  # Последняя ячейка - значение

            if name_elem and value_elem:
                name = name_elem.get_text(strip=True).lower()
                value = value_elem.get_text(strip=True)
                if name and value:
                    attributes[name] = value

    return attributes


def _detect_rich_content(description_html: str) -> bool:
    """
    Определение наличия rich-контента в описании товара.
    Rich-контент = наличие изображений, таблиц или списков в описании.
    """
    if not description_html:
        return False

    soup = BeautifulSoup(description_html, "html.parser")

    # Проверка на изображения
    images = soup.find_all("img")
    if images:
        logger.debug("Rich content: найдено %d изображений", len(images))
        return True

    # Проверка на таблицы
    tables = soup.find_all("table")
    if tables:
        logger.debug("Rich content: найдено %d таблиц", len(tables))
        return True

    # Проверка на списки
    lists = soup.find_all(["ul", "ol"])
    if lists:
        logger.debug("Rich content: найдено %d списков", len(lists))
        return True

    return False


def parse_product_page(page_html: str, sku: str) -> Dict[str, Any]:
    """
    Полное извлечение данных о товаре из HTML-страницы.

    Алгоритм:
    1. Парсинг JSON-LD (наиболее надёжный источник)
    2. Парсинг встроенных JSON (window.__NUXT__, etc.)
    3. Парсинг HTML-элементов (селекторы)
    4. Объединение данных и заполнение пропусков

    Args:
        page_html: HTML-код страницы товара
        sku: Артикул товара

    Returns:
        Словарь с извлечёнными данными
    """
    logger.info("Парсинг карточки товара SKU: %s", sku)

    soup = BeautifulSoup(page_html, "html.parser")
    result: Dict[str, Any] = {"sku": sku}

    # 1. Извлечение из JSON-LD (наиболее надёжный источник)
    logger.debug("Поиск JSON-LD данных...")
    json_ld = _extract_json_ld(soup)
    if json_ld:
        json_ld_data = _extract_from_json_ld(json_ld, soup)
        result.update(json_ld_data)
        logger.debug("JSON-LD данные найдены: %s", list(json_ld_data.keys()))
    else:
        logger.debug("JSON-LD данные не найдены")

    # 2. Извлечение из встроенных JSON
    product_attributes = {}
    embedded_data = _extract_embedded_json(page_html)
    if embedded_data:
        product_attributes = _get_product_attributes(embedded_data)
        if product_attributes:
            logger.debug("Атрибуты из embedded JSON: %s", list(product_attributes.keys())[:10])

    # 3. Извлечение из HTML (фоллбэк)
    logger.debug("Поиск данных в HTML-элементах...")
    html_data = _extract_from_html(soup, page_html)
    result.update(html_data)

    # 4. Извлечение атрибутов из HTML-таблиц (фоллбэк)
    html_attributes = _extract_attributes_from_html(soup)
    if html_attributes:
        logger.debug("Атрибуты из HTML: %s", list(html_attributes.keys())[:10])

    # 5. Объединение атрибутов (embedded JSON имеет приоритет)
    all_attributes = {**html_attributes, **product_attributes}

    # Ищем цвет
    if "color" not in result:
        for key, value in all_attributes.items():
            if any(word in key.lower() for word in ["цвет", "color", "colour"]):
                result["color"] = value
                break

    # Ищем материал
    if "material" not in result:
        for key, value in all_attributes.items():
            if any(word in key.lower() for word in ["material", "материал"]):
                result["material"] = value
                break

    # Ищем артикул производителя / комплектацию
    if "art_set" not in result:
        for key, value in all_attributes.items():
            if any(word in key.lower() for word in ["арт", "manufacturer", "производитель", "комплект", "article"]):
                result["art_set"] = value
                break

    # 6. Проверка rich content
    description_html = result.pop("_description_html", None)
    result["has_rich_content"] = _detect_rich_content(description_html)

    # 7. Фоллбэки: если что-то не нашли, ставим None
    for field in ["title", "price", "rating", "reviews_total", "cover_image",
                   "photos_seller", "videos_seller", "color", "material", "art_set"]:
        if field not in result:
            result[field] = None

    # Логирование результатов
    logger.info(
        "Результат парсинга SKU %s: title=%s, price=%s, rating=%s, reviews=%s",
        sku,
        result.get("title")[:50] if result.get("title") else None,
        result.get("price"),
        result.get("rating"),
        result.get("reviews_total"),
    )

    return result
