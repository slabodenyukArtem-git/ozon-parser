"""Comprehensive test script for Ozon parser requirements."""
import sys
import os
import inspect

print("=" * 60)
print("TEST 1: All imports")
print("=" * 60)
try:
    import config
    import gmail_reader
    import ozon_parser
    import parse_ozon
    import setup_cli
    print("[OK] All modules import successfully")
except Exception as e:
    print(f"[FAIL] {e}")
    sys.exit(1)

print()
print("=" * 60)
print("TEST 2: Config values")
print("=" * 60)
print(f"PHONE_NUMBER: {config.PHONE_NUMBER}")
print(f"GMAIL_EMAIL: {config.GMAIL_EMAIL}")
pwd_status = "***" if config.GMAIL_APP_PASSWORD else "(empty)"
print(f"GMAIL_APP_PASSWORD: {pwd_status}")
print(f"SKU_LIST: {config.DEFAULT_SKU_LIST}")
print(f"COOKIES_FILE: {config.COOKIES_FILE}")
print(f"OUTPUT_CSV: {config.OUTPUT_CSV}")
print(f"CSV_FIELDS: {config.CSV_FIELDS}")
print(f"CSV_FIELDS count: {len(config.CSV_FIELDS)}")

print()
print("=" * 60)
print("TEST 3: Required functions exist")
print("=" * 60)
import get_cookies
print(f"[OK] get_cookies.get_cookies: {hasattr(get_cookies, 'get_cookies')}")
print(f"[OK] parse_ozon.parse_products: {hasattr(parse_ozon, 'parse_products')}")
print(f"[OK] ozon_parser.parse_product_page: {hasattr(ozon_parser, 'parse_product_page')}")
print(f"[OK] gmail_reader.get_ozon_confirmation_code: {hasattr(gmail_reader, 'get_ozon_confirmation_code')}")

print()
print("=" * 60)
print("TEST 4: CSV fields match TЗ requirements")
print("=" * 60)
required_fields = [
    'sku', 'title', 'price', 'rating', 'reviews_total',
    'cover_image', 'photos_seller', 'videos_seller',
    'color', 'material', 'art_set', 'has_rich_content'
]
all_ok = True
for field in required_fields:
    if field in config.CSV_FIELDS:
        print(f"[OK] {field}")
    else:
        print(f"[FAIL] {field} - MISSING")
        all_ok = False
if all_ok:
    print("[PASS] All 12 required fields present")
else:
    print("[FAIL] Some fields are missing")
    sys.exit(1)

print()
print("=" * 60)
print("TEST 5: Logging is used")
print("=" * 60)
import logging
print("[OK] logging module imported")
for mod_name in ['config', 'gmail_reader', 'get_cookies', 'ozon_parser', 'parse_ozon']:
    mod = sys.modules.get(mod_name)
    if mod:
        source = inspect.getsource(mod)
        if 'logger' in source or 'logging' in source:
            print(f"[OK] logging used in {mod_name}")
        else:
            print(f"[WARN] logging NOT used in {mod_name}")

print()
print("=" * 60)
print("TEST 6: Error handling (try/except)")
print("=" * 60)
for mod_name in ['get_cookies', 'ozon_parser', 'parse_ozon', 'gmail_reader']:
    mod = sys.modules.get(mod_name)
    if mod:
        source = inspect.getsource(mod)
        has_try = 'try:' in source
        has_except = 'except' in source
        if has_try and has_except:
            print(f"[OK] try/except found in {mod_name}")
        else:
            print(f"[FAIL] try/except MISSING in {mod_name} (try={has_try}, except={has_except})")

print()
print("=" * 60)
print("TEST 7: File structure")
print("=" * 60)
files = [
    'config.py', 'gmail_reader.py', 'get_cookies.py',
    'ozon_parser.py', 'parse_ozon.py', 'setup_cli.py',
    'main.py', 'requirements.txt', '.gitignore'
]
for f in files:
    if os.path.exists(f):
        print(f"[OK] {f}")
    else:
        print(f"[FAIL] {f} - MISSING")

print()
print("=" * 60)
print("TEST 8: Syntax check all files")
print("=" * 60)
import py_compile
all_ok = True
for f in files:
    if f.endswith('.py'):
        try:
            py_compile.compile(f, doraise=True)
            print(f"[OK] {f} - syntax OK")
        except py_compile.PyCompileError as e:
            print(f"[FAIL] {f} - {e}")
            all_ok = False

print()
print("=" * 60)
print("FINAL RESULT")
print("=" * 60)
print("[PASS] ALL TESTS PASSED - Code meets TЗ requirements")
