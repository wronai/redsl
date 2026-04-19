.PHONY: help install dev-install test test-fast test-all lint type-check format format-check docker-up docker-down docker-build run run-local clean build publish publish-test bump-patch bump-minor bump-major

PYTHON := python3
PIP := pip
DOCKER_COMPOSE := docker-compose

help:
	@echo "Dostępne komendy:"
	@echo "  install       - Instalacja zależności produkcyjnych"
	@echo "  dev-install   - Instalacja zależności deweloperskich"
	@echo "  test          - Uruchomienie testów pytest (bez slow)"
	@echo "  test-fast     - Szybkie testy (bez slow/integration/e2e)"
	@echo "  test-all      - Wszystkie testy włącznie z slow"
	@echo "  lint          - Sprawdzenie lintingu ruff"
	@echo "  type-check    - Sprawdzenie typów mypy"
	@echo "  format        - Formatowanie kodu ruff"
	@echo "  format-check  - Sprawdzenie formatowania kodu"
	@echo "  docker-up     - Uruchomienie usług Docker"
	@echo "  docker-down   - Zatrzymanie usług Docker"
	@echo "  docker-build  - Budowanie obrazów Docker"
	@echo "  run           - Uruchomienie aplikacji w Docker"
	@echo "  run-local     - Uruchomienie aplikacji lokalnie"
	@echo "  clean         - Czyszczenie plików tymczasowych"
	@echo ""
	@echo "📦 Building & Release:"
	@echo "  build         - Build distribution packages"
	@echo "  publish       - Publish to PyPI (requires credentials)"
	@echo "  publish-test  - Publish to TestPyPI"
	@echo "  bump-patch    - Bump patch version"
	@echo "  bump-minor    - Bump minor version"
	@echo "  bump-major    - Bump major version"

install:
	$(PIP) install -r requirements.txt

dev-install:
	$(PIP) install -r requirements.txt
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest tests/ -v -m "not slow"

test-fast:
	$(PYTHON) -m pytest tests/ -q -m "not slow and not integration and not e2e"

test-all:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check redsl/ tests/

type-check:
	$(PYTHON) -m mypy redsl/

format:
	$(PYTHON) -m ruff format redsl/ tests/
	$(PYTHON) -m ruff check --fix redsl/ tests/

format-check:
	$(PYTHON) -m ruff format --check redsl/ tests/

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-build:
	$(DOCKER_COMPOSE) build

run: docker-up

run-local:
	$(PYTHON) -m uvicorn redsl.api:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf refactor_output/ build/ dist/ *.egg-info 2>/dev/null || true

build:
	rm -rf build/ dist/ *.egg-info
	$(PYTHON) -m build
	@echo "✓ Build complete - check dist/"

bump-patch:
	@current=$$(cat VERSION); \
	major=$$(echo $$current | cut -d. -f1); \
	minor=$$(echo $$current | cut -d. -f2); \
	patch=$$(echo $$current | cut -d. -f3); \
	new_patch=$$((patch + 1)); \
	new_version="$${major}.$${minor}.$${new_patch}"; \
	echo "$$new_version" > VERSION; \
	sed -i "s/version = \"$$current\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "🔢 Bumped version: $$current → $$new_version"

bump-minor:
	@current=$$(cat VERSION); \
	major=$$(echo $$current | cut -d. -f1); \
	minor=$$(echo $$current | cut -d. -f2); \
	new_minor=$$((minor + 1)); \
	new_version="$${major}.$${new_minor}.0"; \
	echo "$$new_version" > VERSION; \
	sed -i "s/version = \"$$current\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "🔢 Bumped version: $$current → $$new_version"

bump-major:
	@current=$$(cat VERSION); \
	major=$$(echo $$current | cut -d. -f1); \
	new_major=$$((major + 1)); \
	new_version="$${new_major}.0.0"; \
	echo "$$new_version" > VERSION; \
	sed -i "s/version = \"$$current\"/version = \"$$new_version\"/" pyproject.toml; \
	echo "🔢 Bumped version: $$current → $$new_version"

publish-test: build
	@echo "🚀 Publishing to TestPyPI..."
	@bash -c 'if [ -z "$${TWINE_USERNAME}" ] && [ -z "$${TWINE_PASSWORD}" ] && [ -z "$${PYPI_API_TOKEN}" ] && [ ! -f "$${HOME}/.pypirc" ]; then \
		echo "⚠️  No PyPI credentials found. Set TWINE_USERNAME and TWINE_PASSWORD, PYPI_API_TOKEN, or configure ~/.pypirc"; \
		echo "   Example: TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-xxx make publish-test"; \
		echo "   Skipping publish-test."; \
		exit 0; \
	else \
		$(PYTHON) -m venv publish-test-env && \
		publish-test-env/bin/pip install twine && \
		publish-test-env/bin/python -m twine upload --repository testpypi dist/* && \
		echo "✓ Published to TestPyPI" || \
		echo "✗ Publish failed"; \
		rm -rf publish-test-env; \
	fi'

publish: build
	@echo "🚀 Publishing to PyPI..."
	@bash -c 'if [ -z "$${TWINE_USERNAME}" ] && [ -z "$${TWINE_PASSWORD}" ] && [ -z "$${PYPI_API_TOKEN}" ] && [ ! -f "$${HOME}/.pypirc" ]; then \
		echo "⚠️  No PyPI credentials found. Set TWINE_USERNAME and TWINE_PASSWORD, PYPI_API_TOKEN, or configure ~/.pypirc"; \
		echo "   Example: TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-xxx make publish"; \
		echo "   Skipping publish."; \
		exit 0; \
	else \
		$(PYTHON) -m venv publish-env; \
		publish-env/bin/pip install twine; \
		publish-env/bin/python -m twine upload dist/* && \
		echo "✓ Published to PyPI" || \
		echo "✗ Publish failed"; \
		rm -rf publish-env; \
	fi'
