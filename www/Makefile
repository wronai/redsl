PHP_PORT := 7000
API_PORT := 8002
PHP_DOCROOT := .
PHP_PID_FILE := .php-server.pid

.PHONY: help start stop status test

help:
	@echo "Dostepne komendy:"
	@echo "  make start  - Uruchom PHP serwer (port $(PHP_PORT)) + API (port $(API_PORT))"
	@echo "  make stop   - Zatrzymaj PHP serwer i API"
	@echo "  make status - Sprawdz status serwerow"
	@echo "  make test   - Uruchom PHPUnit"

start: stop
	@echo "Starting PHP server on port $(PHP_PORT)..."
	@php -S 0.0.0.0:$(PHP_PORT) -t $(PHP_DOCROOT) > /dev/null 2>&1 & echo $$! > $(PHP_PID_FILE)
	@sleep 1
	@echo "PHP server PID: $$(cat $(PHP_PID_FILE))"
	@echo "Access: http://localhost:$(PHP_PORT)/marketing/"
	@echo ""
	@echo "To start API backend, run from redsl root:"
	@echo "  cd ../ && uvicorn redsl.api:app --reload --port $(API_PORT)"

stop:
	@echo "Stopping PHP server on port $(PHP_PORT)..."
	@if [ -f $(PHP_PID_FILE) ]; then kill $$(cat $(PHP_PID_FILE)) 2>/dev/null || true; rm -f $(PHP_PID_FILE); fi
	@lsof -ti :$(PHP_PORT) | xargs -r kill 2>/dev/null || true
	@echo "Port $(PHP_PORT) freed."

status:
	@echo "PHP server (port $(PHP_PORT)):"
	@curl -s -o /dev/null -w "%{http_code}\n" http://localhost:$(PHP_PORT)/marketing/ || echo "DOWN"
	@echo "API (port $(API_PORT)):"
	@curl -s -o /dev/null -w "%{http_code}\n" http://localhost:$(API_PORT)/health || echo "DOWN"

test:
	@cd /home/tom/github/semcod/redsl/www && php -d extension=/tmp/php8.4-xml-extracted/usr/lib/php/20240924/xml.so -d extension=/tmp/php8.4-xml-extracted/usr/lib/php/20240924/dom.so -d extension=/tmp/php8.4-xml-extracted/usr/lib/php/20240924/simplexml.so -d extension=/tmp/php8.4-xml-extracted/usr/lib/php/20240924/xmlwriter.so vendor/bin/phpunit tests/MarketingHubTest.php
