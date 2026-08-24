"""
Генерация случайных данных для регистрации.

ParaBank — общая публичная база: username должен быть уникальным среди
ВСЕХ, кто когда-либо тестировал этот сайт по всему миру. Подтверждено
экспериментально (см. README, раздел "Особенности сайта"): проверка
уникальности на сервере ведёт себя как нечёткое совпадение по подстроке,
а не точное сравнение — ЛЮБОЙ username с префиксом вроде "qa_", "test_",
"e2e_" стабильно получает "This username already exists.", даже если
такая строка гарантированно никогда раньше не встречалась. Поэтому
генерируем чисто случайную буквенно-цифровую строку без семантического
префикса — только это даёт стабильную регистрацию.
"""

import random
import string
from dataclasses import dataclass

FIRST_NAMES = ["Ivan", "Anna", "Sergey", "Olga", "Dmitry", "Maria"]
LAST_NAMES = ["Petrov", "Ivanova", "Sidorov", "Kuznetsova", "Volkov", "Orlova"]


@dataclass
class NewCustomerData:
    first_name: str
    last_name: str
    street: str
    city: str
    state: str
    zip_code: str
    phone_number: str
    ssn: str
    username: str
    password: str


def _random_username() -> str:
    # Без разделителей вроде "_" и без семантического префикса — только
    # [a-z0-9]. Достаточно длинная случайная строка, чтобы не бояться
    # коллизий даже при плотном параллельном запуске (pytest-xdist).
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=20))


def generate_new_customer() -> NewCustomerData:
    return NewCustomerData(
        first_name=random.choice(FIRST_NAMES),
        last_name=random.choice(LAST_NAMES),
        street=f"{random.randint(1, 999)} Test Street",
        city="Testville",
        state="TS",
        zip_code=str(random.randint(10000, 99999)),
        phone_number=f"555{random.randint(1000000, 9999999)}",
        ssn=str(random.randint(100000000, 999999999)),
        username=_random_username(),
        password=f"Demo{random.randint(1000, 9999)}Pass!",
    )
