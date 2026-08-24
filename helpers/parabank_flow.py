"""
Переиспользуемые шаги для ParaBank.

Особенность сайта, подтверждённая вручную перед написанием этого файла
(порт из TypeScript-версии этого же проекта — все находки уже проверены
там на реальном DOM/сети, см. README): кнопки "Open New Account" и
"Apply Now" — НЕ submit, а <button type="button">, обрабатывающие клик
через AJAX и подменяющие содержимое страницы без полной навигации.
Обычный Playwright click() отрабатывает корректно, но результат
проверяем через ожидание конкретного текста, а не через wait_for_url —
URL при AJAX-подмене не меняется.
"""

from dataclasses import dataclass
from typing import Literal

from playwright.sync_api import Page, expect

from helpers.test_data import NewCustomerData

AccountType = Literal["CHECKING", "SAVINGS"]


def register_new_customer(page: Page, data: NewCustomerData) -> None:
    page.goto("register.htm")

    # ВНИМАНИЕ: id-шники формы содержат точки ("customer.firstName") —
    # в CSS-локаторе точка после # читается как разделитель класса, а не
    # как часть id ("#customer.firstName" === id=customer класс=firstName).
    # Нужен атрибутный селектор, а не голый #id.
    page.locator('[id="customer.firstName"]').fill(data.first_name)
    page.locator('[id="customer.lastName"]').fill(data.last_name)
    page.locator('[id="customer.address.street"]').fill(data.street)
    page.locator('[id="customer.address.city"]').fill(data.city)
    page.locator('[id="customer.address.state"]').fill(data.state)
    page.locator('[id="customer.address.zipCode"]').fill(data.zip_code)
    page.locator('[id="customer.phoneNumber"]').fill(data.phone_number)
    page.locator('[id="customer.ssn"]').fill(data.ssn)

    username_field = page.locator('[id="customer.username"]')
    username_field.fill(data.username)
    # Уводим фокус с поля явно (Tab) — подстраховка на случай debounced
    # AJAX-проверки на blur (см. TS-версию проекта для деталей находки).
    username_field.press("Tab")

    page.locator('[id="customer.password"]').fill(data.password)
    page.locator("#repeatedPassword").fill(data.password)

    page.get_by_role("button", name="Register").click()

    # "This username already exists" — реальный кейс на общей публичной
    # базе (см. helpers/test_data.py), поэтому явно проверяем позитивный
    # исход, а не просто ждём любую следующую страницу.
    expect(page.get_by_text("Your account was created successfully.")).to_be_visible(timeout=10_000)


def login(page: Page, username: str, password: str) -> None:
    page.goto("index.htm")
    page.locator('input[name="username"]').fill(username)
    page.locator('input[name="password"]').fill(password)
    page.get_by_role("button", name="Log In").click()
    # "Welcome ..." — текст в левой панели сессии (<p class="smallText">),
    # не заголовок (подтверждено дампом реального DOM).
    expect(page.locator("#leftPanel")).to_contain_text("Welcome", timeout=10_000)


def open_new_account(page: Page, account_type: AccountType) -> str:
    """Открывает новый счёт и возвращает его номер.

    РЕАЛЬНАЯ гонка на стороне сайта: список #fromAccountId заполняется
    отдельным асинхронным AJAX-запросом (getAccounts()) уже ПОСЛЕ рендера
    страницы. Обработчик клика читает accounts.selectedOption.id без
    проверки на null — если кликнуть раньше, чем этот запрос успеет
    отработать, JS падает с исключением и submit() вообще не отправляет
    запрос на создание счёта (кнопка "нажимается", эффекта — ноль).
    Поэтому явно ждём, что список счетов реально заполнился, прежде чем
    кликать.
    """
    page.goto("openaccount.htm")

    page.locator("#fromAccountId option").first.wait_for(state="attached", timeout=10_000)

    page.locator("#type").select_option("0" if account_type == "CHECKING" else "1")

    page.get_by_role("button", name="Open New Account").click()

    expect(page.get_by_text("Account Opened!")).to_be_visible(timeout=10_000)

    account_link = page.locator("#newAccountId")
    expect(account_link).to_be_visible()
    account_number = (account_link.text_content() or "").strip()

    if not account_number:
        raise RuntimeError('Не удалось прочитать номер нового счёта после "Account Opened!"')

    return account_number


def transfer_funds(page: Page, amount: float, from_account_id: str, to_account_id: str) -> None:
    page.goto("transfer.htm")

    page.locator("#amount").fill(str(amount))
    page.locator("#fromAccountId").select_option(from_account_id)
    page.locator("#toAccountId").select_option(to_account_id)

    page.get_by_role("button", name="Transfer").click()

    expect(page.get_by_text("Transfer Complete!")).to_be_visible(timeout=10_000)


@dataclass
class LoanRequestResult:
    status: Literal["Approved", "Denied"]
    reason_text: str


def request_loan(page: Page, amount: float, down_payment: float, from_account_id: str) -> LoanRequestResult:
    """Заявка на кредит — единственный сценарий на сайте с явным решением
    Approved/Denied, ближайший аналог "заявление → решение" из закрытых
    корпоративных проектов. Тоже AJAX-кнопка ("Apply Now"), поэтому ждём
    заголовок результата, а не навигацию.
    """
    page.goto("requestloan.htm")

    page.locator("#amount").fill(str(amount))
    page.locator("#downPayment").fill(str(down_payment))
    page.locator("#fromAccountId").select_option(from_account_id)

    page.get_by_role("button", name="Apply Now").click()

    expect(page.get_by_text("Loan Request Processed")).to_be_visible(timeout=10_000)

    status_text = (page.locator("#loanStatus").text_content() or "").strip()
    status: Literal["Approved", "Denied"] = "Approved" if status_text == "Approved" else "Denied"

    # На странице результата ОБА блока (одобрено/отказано) присутствуют в
    # DOM одновременно, виден только актуальный (второй скрыт через
    # display:none) — читаем нужный явно по status, а не пытаемся угадать
    # текстом.
    if status == "Denied":
        reason_text = (page.locator("#loanRequestDenied").text_content() or "").strip()
    else:
        reason_text = (page.locator("#loanRequestApproved").text_content() or "").strip()

    return LoanRequestResult(status=status, reason_text=reason_text)
