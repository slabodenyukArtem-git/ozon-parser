# Ozon Product Page - CSS Selectors & JSON Data Structures Analysis

## 1. Architecture Overview

Ozon uses **Nuxt.js 3** (Vue 3) SPA architecture with SSR (Server-Side Rendering).
Product data is embedded in multiple formats:

```
HTML Page
├── <script type="application/ld+json">       # JSON-LD (Schema.org)
├── <script type="application/json">          # Embedded JSON data
├── window.__NUXT__                           # Nuxt state
├── <meta property="og:*">                    # Open Graph metadata
└── HTML elements with data-* attributes      # UI components
```

---

## 2. JSON-LD Schema Patterns

Ozon uses **Schema.org Product** structured data in JSON-LD format:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Product",
  "@graph": [
    {
      "@type": "Product",
      "name": "Полное название товара",
      "sku": "1234567890",
      "image": [
        "https://basket-12.wbbasket.ru/vol1234/part1234/123456789/images/big/1.webp",
        "https://basket-12.wbbasket.ru/vol1234/part1234/123456789/images/big/2.webp"
      ],
      "description": "Описание товара",
      "brand": {
        "@type": "Brand",
        "name": "Бренд товара"
      },
      "offers": {
        "@type": "Offer",
        "price": "1299.00",
        "priceCurrency": "RUB",
        "availability": "https://schema.org/InStock"
      },
      "aggregateRating": {
        "@type": "AggregateRating",
        "ratingValue": "4.8",
        "reviewCount": "1234",
        "bestRating": "5",
        "worstRating": "1"
      },
      "mpn": "ART-12345",
      "additionalProperty": [
        {
          "@type": "PropertyValue",
          "name": "Цвет",
          "value": "Красный"
        },
        {
          "@type": "PropertyValue",
          "name": "Материал",
          "value": "Хлопок"
        }
      ]
    }
  ]
}
</script>
```

### Key JSON-LD fields mapping:

| Поле | JSON-LD путь |
|------|-------------|
| sku | `@graph[*].sku` или `@graph[*].additionalProperty[?name="Артикул"]` |
| title | `@graph[*].name` |
| price | `@graph[*].offers.price` |
| rating | `@graph[*].aggregateRating.ratingValue` |
| reviews_total | `@graph[*].aggregateRating.reviewCount` |
| cover_image | `@graph[*].image[0]` |
| color | `@graph[*].additionalProperty[?name="Цвет"].value` |
| material | `@graph[*].additionalProperty[?name="Материал"].value` |
| art_set | `@graph[*].mpn` или `additionalProperty[?name="Артикул производителя"]` |

---

## 3. Embedded JSON Patterns

### 3.1 Nuxt.js State (window.__NUXT__)

```javascript
window.__NUXT__ = {
  serverData: {
    product: {
      productInfo: {
        sku: 1234567890,
        name: "Название товара",
        mainInfo: {
          productName: "Полное название",
          brand: { name: "Бренд" },
          vendor: "Производитель"
        },
        pricing: {
          priceWithDiscount: {
            value: 1299,
            currency: "RUB",
            formatted: "1 299 \u20bd"
          },
          price: {
            value: 2999,
            currency: "RUB",
            formatted: "2 999 \u20bd"
          },
          discountPercent: 57
        },
        rating: {
          value: 4.8,
          quantity: 1234
        },
        media: {
          cover: "https://basket-12.wbbasket.ru/.../images/big/1.webp",
          photos: [
            { url: "https://basket-12.wbbasket.ru/.../1.webp" },
            { url: "https://basket-12.wbbasket.ru/.../2.webp" }
          ],
          videos: [
            { url: "https://video.ozon.ru/.../video1.mp4", thumbnail: "..." }
          ]
        },
        characteristics: [
          { name: "Цвет", value: "Красный" },
          { name: "Материал", value: "Хлопок" },
          { name: "Артикул производителя", value: "ART-12345" },
          { name: "Комплектация", value: "1 шт." }
        ]
      }
    }
  }
}
```

### 3.2 Embedded JSON in Script Tags

```html
<script type="application/json" id="__NEXT_DATA__">
{
  "props": {
    "pageProps": {
      "product": {
        "sku": 1234567890,
        "name": "Название товара",
        "price": { "value": 1299, "currency": "RUB" },
        "rating": { "value": 4.8, "quantity": 1234 },
        "media": {
          "cover": "url_to_image",
          "photos": [...],
          "videos": [...]
        },
        "characteristics": [...]
      }
    }
  }
}
</script>
```

### 3.3 Common Embedded Data Patterns

```python
# Patterns to search in page HTML
patterns = [
    r'window\.__NUXT__\s*=\s*({.*?});\s*</script>',
    r'window\.__NEXT_DATA__\s*=\s*({.*?});\s*</script>',
    r'window\.__OZON_PRODUCT_DATA__\s*=\s*({.*?});\s*</script>',
    r'<script type="application/json" id=".*?">(.*?)</script>',
    r'<script type="application/json">(.*?)</script>',
]
```

---

## 4. CSS Selectors for HTML Elements

### 4.1 Basic Product Fields

```python
# SKU
sku_selectors = [
    '[data-field="sku"]',
    '[data-sku]',
    'meta[itemprop="sku"]',
    'script[type="application/ld+json"]',  # parse JSON-LD
]

# Title
title_selectors = [
    'h1',
    '[data-widget="product-title"]',
    '[data-testid="product-title"]',
    'meta[property="og:title"]',
    'meta[name="title"]',
    '[class*="product-title"]',
    '[class*="title"] h1',
]

# Price
price_selectors = [
    '[data-widget="price"] .price-value',
    '[data-testid="price-value"]',
    '[class*="price-main"]',
    '[class*="price-value"]',
    'meta[property="og:price:amount"]',
    'meta[property="product:price:amount"]',
    '[data-widget="price-block"]',
    '[class*="current-price"]',
    '[class*="price"] [class*="value"]',
]

# Rating
rating_selectors = [
    '[data-widget="rating"]',
    '[data-testid="product-rating"]',
    'meta[itemprop="ratingValue"]',
    '[class*="rating-value"]',
    '[class*="rating"] [class*="value"]',
]

# Reviews count
reviews_selectors = [
    '[data-widget="reviews-count"]',
    '[data-testid="reviews-count"]',
    'meta[itemprop="reviewCount"]',
    '[class*="reviews-count"]',
    '[class*="review-count"]',
    '[class*="reviews"] [class*="count"]',
]
```

### 4.2 Image Selectors

```python
# Cover image
cover_image_selectors = [
    'meta[property="og:image"]',
    'meta[itemprop="image"]',
    '[data-widget="product-main-image"]',
    '[data-testid="main-image"]',
    '[class*="main-image"] img',
    '[class*="cover-image"] img',
]

# First image fallback
img_fallback = soup.find("img", itemprop="image")
# Or by class
img_by_class = soup.find("img", class_=re.compile(r"(?i)(main|cover|hero|primary)"))
```

### 4.3 Gallery (Photos & Videos)

```python
# Photos count
photos_selectors = [
    '[data-widget="gallery-photos-count"]',
    '[data-testid="gallery-photos-count"]',
    '[class*="gallery"] [class*="photos"] [class*="count"]',
]

# Videos count
videos_selectors = [
    '[data-widget="gallery-videos-count"]',
    '[data-testid="gallery-videos-count"]',
    '[class*="gallery"] [class*="videos"] [class*="count"]',
]

# Alternative: count gallery items
photos_count = len(soup.select('[class*="gallery"] [class*="slide"]'))
videos_count = len(soup.select('[class*="video"]'))
```

### 4.4 Attributes Table (Color, Material, Art Set)

```python
# Specs/Characteristics block
specs_selectors = [
    '[data-widget="product-specs"]',
    '[data-testid="product-specs"]',
    '[data-widget="characteristics"]',
    '[class*="product-specs"]',
    '[class*="characteristics"]',
    '[class*="specs"]',
]

# Table-based characteristics
table_patterns = [
    # Pattern 1: <tr><td class="name">Цвет</td><td class="value">Красный</td></tr>
    'tr[class*="spec-row"] td[class*="name"]',
    'tr[class*="spec-row"] td[class*="value"]',
    
    # Pattern 2: <dl><dt>Цвет</dt><dd>Красный</dd></dl>
    'dl[class*="specs"] dt',
    'dl[class*="specs"] dd',
    
    # Pattern 3: <div class="spec-item"><span class="label">Цвет</span><span class="data">Красный</span></div>
    '[class*="spec-item"] [class*="label"]',
    '[class*="spec-item"] [class*="data"]',
    
    # Pattern 4: Generic table
    'table[class*="specs"] tr td',
]

# HTML structure patterns for characteristics:
# Pattern A:
# <div class="characteristics">
#   <div class="characteristic-row">
#     <span class="name">Цвет</span>
#     <span class="value">Красный</span>
#   </div>
# </div>

# Pattern B:
# <table class="specs-table">
#   <tr>
#     <td class="attr-name">Цвет</td>
#     <td class="attr-value">Красный</td>
#   </tr>
# </table>

# Pattern C:
# <div class="product-characteristics">
#   <div class="row">
#     <div class="col-name">Материал</div>
#     <div class="col-value">Хлопок</div>
#   </div>
# </div>
```

### 4.5 Rich Content Detection

```python
# Description block selectors
description_selectors = [
    '[data-widget="description"]',
    '[data-testid="description"]',
    '[class*="product-description"]',
    '[class*="description-rich"]',
    '[id*="rich-description"]',
    '[class*="rich-content"]',
]

# Rich content detection:
def has_rich_content(description_html):
    soup = BeautifulSoup(description_html, "html.parser")
    has_images = len(soup.find_all("img")) > 0
    has_tables = len(soup.find_all("table")) > 0
    has_lists = len(soup.find_all(["ul", "ol"])) > 0
    return has_images or has_tables or has_lists
```

---

## 5. HTML Element Class Patterns

Ozon uses BEM-like naming for CSS classes:

```python
# Common class name patterns
class_patterns = {
    # Price
    "price_main": re.compile(r"(?i)(price-main|current-price|price-value)"),
    "price_old": re.compile(r"(?i)(price-old|previous-price|strikethrough)"),
    "price_discount": re.compile(r"(?i)(discount|sale|percent-off)"),
    
    # Rating
    "rating_container": re.compile(r"(?i)(rating|score|stars)"),
    "rating_value": re.compile(r"(?i)(rating-value|score-value|star-rating)"),
    "rating_count": re.compile(r"(?i)(rating-count|review-count|reviews-total)"),
    
    # Gallery
    "gallery": re.compile(r"(?i)(gallery|slider|carousel|images)"),
    "gallery_item": re.compile(r"(?i)(slide|thumb|thumbnail|preview)"),
    "gallery_video": re.compile(r"(?i)(video|play|media)"),
    
    # Description
    "description": re.compile(r"(?i)(description|desc|about|details)"),
    "rich_content": re.compile(r"(?i)(rich|editorial|content|html)"),
    
    # Characteristics
    "specs": re.compile(r"(?i)(specs|characteristics|attributes|properties)"),
    "spec_row": re.compile(r"(?i)(spec-row|attr-row|char-row)"),
    "spec_name": re.compile(r"(?i)(spec-name|attr-name|label|property)"),
    "spec_value": re.compile(r"(?i)(spec-value|attr-value|data|value)"),
    
    # Images
    "main_image": re.compile(r"(?i)(main-image|cover|hero|primary)"),
    "gallery_image": re.compile(r"(?i)(gallery|thumb|thumbnail|preview|slide)"),
}
```

---

## 6. Data URL Patterns

Ozon stores images and media on CDN:

```python
# Image URL patterns
image_patterns = {
    # Wildberries CDN (Ozon uses WB infrastructure)
    "basket_cdn": re.compile(r"https://basket-\d+\.wbbasket\.ru/.*?/images/(big|medium|small)/.*?\.(webp|jpg|jpeg|png)"),
    
    # Ozon CDN
    "ozon_cdn": re.compile(r"https://(img|media)\.ozon\.ru/.*?\.(webp|jpg|jpeg|png)"),
    
    # Video URLs
    "video_cdn": re.compile(r"https://video\.ozon\.ru/.*?\.(mp4|m3u8)"),
}

# Image URL transformation
# Ozon supports size parameters in URLs:
# /images/big/ -> /images/medium/ -> /images/small/
# Or use query params: ?width=800&height=600
```

---

## 7. Priority Strategy for Data Extraction

```
PRIORITY ORDER:
┌─────────────────────────────────────────────────────────┐
│ 1. JSON-LD (most reliable, structured)                  │
│    - <script type="application/ld+json">                 │
│    - Schema.org Product type                             │
│                                                         │
│ 2. Embedded JSON (complete data)                         │
│    - window.__NUXT__                                     │
│    - <script type="application/json">                    │
│    - Contains full product object                        │
│                                                         │
│ 3. Meta tags (quick fallback)                            │
│    - og:title, og:image, og:price:amount                │
│    - itemprop="*"                                       │
│                                                         │
│ 4. HTML selectors (UI-based, may break)                  │
│    - data-widget="*" attributes                          │
│    - data-testid="*" attributes                          │
│    - Class-based selectors                               │
│                                                         │
│ 5. URL-based (last resort)                               │
│    - SKU from URL path                                   │
│    - Title from URL slug                                │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Common Anti-Bot Considerations

Ozon uses **ABT (AntiBot Technology)**:

```python
# Direct requests to www.ozon.ru return 403
# Solutions:
# 1. Playwright/Puppeteer with stealth (headless browser)
# 2. Use cookies from authenticated session
# 3. data.ozon.ru requires login (phone + code)
# 4. Add realistic headers
# 5. Add delays between requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}
```

---

## 9. Field Extraction Summary

| # | Поле | Primary Source | Fallback Sources |
|---|------|---------------|-----------------|
| 1 | sku | JSON-LD `@graph[*].sku` | URL path, `[data-sku]` |
| 2 | title | JSON-LD `@graph[*].name` | `<h1>`, `og:title` |
| 3 | price | JSON-LD `offers.price` | `[class*="price-value"]` |
| 4 | rating | JSON-LD `aggregateRating.ratingValue` | `[class*="rating-value"]` |
| 5 | reviews_total | JSON-LD `aggregateRating.reviewCount` | `[class*="review-count"]` |
| 6 | cover_image | JSON-LD `image[0]` | `og:image`, `[class*="main-image"]` |
| 7 | photos_seller | Embedded JSON `media.photos.length` | `[class*="gallery"] [class*="photos"]` |
| 8 | videos_seller | Embedded JSON `media.videos.length` | `[class*="gallery"] [class*="videos"]` |
| 9 | color | JSON-LD `additionalProperty[?name="Цвет"]` | Specs table |
| 10 | material | JSON-LD `additionalProperty[?name="Материал"]` | Specs table |
| 11 | art_set | JSON-LD `mpn` or `additionalProperty` | Specs table |
| 12 | has_rich_content | HTML analysis of description | Count `<img>`, `<table>`, `<ul>` |
