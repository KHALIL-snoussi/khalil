.PHONY: run test format build clean install

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run:
	uvicorn app:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v

format:
	ruff check --fix .
	black .

lint:
	ruff check .
	black --check .

build:
	docker build -t diamond-backend .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
