default: check

check: lint test compat

test:
    uv run pytest

lint:
    uv run ruff check

fmt:
    uv run ruff format

compat:
    uv run vermin -t=3.6- resources.py
