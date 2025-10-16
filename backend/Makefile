.PHONY: help install test coverage lint typecheck run clean docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make coverage     - Run tests with coverage"
	@echo "  make lint         - Run linters"
	@echo "  make typecheck    - Run type checking"
	@echo "  make run          - Run development server"
	@echo "  make prod         - Run production server"
	@echo "  make clean        - Clean cache files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/unit -v

coverage:
	pytest --cov=app --cov-report=html --cov-report=term tests/unit
	@echo "Coverage report: htmlcov/index.html"

lint:
	@echo "Running flake8..."
	flake8 app/ tests/ --max-line-length=120 --ignore=E501,W503 || true
	@echo "Running black..."
	black --check app/ tests/ || true

typecheck:
	mypy app/

run:
	python wsgi.py

prod:
	gunicorn -c gunicorn.conf.py wsgi:app

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache

docker-build:
	docker build -t tepure-api:latest .

docker-run:
	docker run -p 8080:8080 --env-file .env tepure-api:latest
