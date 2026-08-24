# Пустой conftest.py в корне проекта — его наличие заставляет pytest
# добавить корень проекта в sys.path, что нужно для импортов вида
# `from helpers.parabank_flow import ...` из tests/*.py (helpers/ лежит
# рядом с tests/, а не внутри неё).
