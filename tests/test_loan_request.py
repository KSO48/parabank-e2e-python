"""
ЗАЯВКА НА КРЕДИТ - единственный сценарий на ParaBank с явным решением
Approved/Denied, ближайший открытый аналог "заявление -> решение" из
закрытых корпоративных проектов. Два теста ниже намеренно направлены в
разные исходы одним и тем же механизмом (размер первоначального взноса
относительно баланса счёта), а не моком ответа сервера -
свежезарегистрированный клиент получает стартовый баланс ~$400+ на первом
счёте (подтверждено вручную перед написанием теста), поэтому:
  - маленький взнос -> одобрено
  - взнос многократно больше баланса -> отказано
"""

from playwright.sync_api import Page

from helpers.parabank_flow import register_new_customer, request_loan
from helpers.test_data import generate_new_customer


def _register_and_get_account_id(page: Page) -> str:
    customer = generate_new_customer()
    register_new_customer(page, customer)

    page.goto("overview.htm")
    account_id = (page.locator("#accountTable a").first.text_content() or "").strip()
    assert account_id != ""
    return account_id


def test_loan_approved_when_down_payment_within_balance(page: Page):
    account_id = _register_and_get_account_id(page)

    result = request_loan(page, amount=100, down_payment=0, from_account_id=account_id)

    assert result.status == "Approved"


def test_loan_denied_when_down_payment_exceeds_balance(page: Page):
    account_id = _register_and_get_account_id(page)

    result = request_loan(page, amount=50_000, down_payment=40_000, from_account_id=account_id)

    assert result.status == "Denied"
    assert "sufficient funds" in result.reason_text
