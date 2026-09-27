"""Optional browser check: pip install playwright; requires Google Chrome."""
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django

django.setup()
from django.contrib.auth import get_user_model
from leads.models import Lead
from playwright.sync_api import sync_playwright

username = 'browser-' + secrets.token_hex(6)
password = secrets.token_urlsafe(24)
user = get_user_model().objects.create_user(username, password=password)
lead_name = 'Browser check ' + username
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto('http://127.0.0.1:8000/')
        page.locator('[name=username]').fill(username)
        page.locator('[name=password]').fill(password)
        page.get_by_role('button', name='Kirish').click()
        page.get_by_role('link', name='＋ Yangi lead', exact=True).click()
        page.locator('[name=name]').fill(lead_name)
        page.locator('[name=phone]').fill('+998901234567')
        page.get_by_role('button', name='Saqlash').click()
        page.locator('[name=status]').select_option('Won')
        page.get_by_role('button', name='Statusni yangilash').click()
        page.get_by_role('link', name='Tahrirlash ↗').click()
        page.locator('[name=source]').fill('Browser')
        page.get_by_role('button', name='Saqlash').click()
        page.get_by_role('link', name='← Leadlar ro‘yxati').click()
        page.locator('[name=search]').fill(lead_name)
        page.locator('[name=status]').select_option('Won')
        page.get_by_role('button', name='Qidirish').click()
        assert page.locator('tbody tr').count() == 1
        assert lead_name in page.locator('tbody').inner_text()
        page.screenshot(path='/tmp/minicrm-desktop.png', full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.screenshot(path='/tmp/minicrm-mobile.png', full_page=True)
        page.get_by_role('link', name=lead_name, exact=False).first.click()
        page.get_by_role('link', name='Leadni o‘chirish').click()
        page.get_by_role('button', name='Ha, o‘chirish').click()
        page.get_by_role('button', name='Chiqish').click()
        page.wait_for_url('**/accounts/login/')
        assert not errors, errors
        browser.close()
        print('PASS: browser login, create, edit, status, search/filter, delete, logout; desktop/mobile; no JS errors.')
    assert not Lead.objects.filter(name=lead_name).exists()
finally:
    Lead.objects.filter(name=lead_name).delete()
    user.delete()
