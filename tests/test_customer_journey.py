"""
ПОЛНЫЙ ПУТЬ КЛИЕНТА: регистрация -> второй счёт -> перевод между счетами

Каждый прогон создаёт СВОЕГО уникального пользователя (см.
helpers/test_data.py) - сайт публичный и общий для всех, кто его
тестирует, поэтому изоляция теста держится на уникальности имени
пользователя, а не на выделенном тестовом окружении.
"""

from playwright.sync_api import Page, expect

from helpers.parabank_flow import login, open_new_account, register_new_customer, transfer_funds
from helpers.test_data import generate_new_customer


def test_registration_second_account_transfer(page: Page):
    customer = generate_new_customer()

    register_new_customer(page, customer)
    expect(page.locator("#leftPanel")).to_contain_text(f"Welcome {customer.first_name} {customer.last_name}")

    # Читаем номер счёта, созданного автоматически при регистрации
    page.goto("overview.htm")
    first_account_link = page.locator("#accountTable a").first
    expect(first_account_link).to_be_visible()
    checking_account_id = (first_account_link.text_content() or "").strip()
    assert checking_account_id != ""

    # Открываем второй счёт (SAVINGS)
    savings_account_id = open_new_account(page, "SAVINGS")
    assert savings_account_id != checking_account_id

    # Переводим средства с текущего счёта на новый
    transfer_funds(page, amount=50, from_account_id=checking_account_id, to_account_id=savings_account_id)

    # Проверяем, что оба счёта видны в обзоре
    page.goto("overview.htm")
    expect(page.locator("#accountTable")).to_contain_text(checking_account_id)
    expect(page.locator("#accountTable")).to_contain_text(savings_account_id)

    # Логаут и повторный логин под тем же пользователем
    page.get_by_role("link", name="Log Out").click()
    login(page, customer.username, customer.password)
