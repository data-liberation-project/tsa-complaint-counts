.PHONY: README.md venv data

PYTHON_DIRS=scripts

requirements.txt: requirements.in
	pip-compile requirements.in

venv:
	python -m venv venv
	venv/bin/pip install -r requirements.txt

format:
	black $(PYTHON_DIRS)
	isort $(PYTHON_DIRS)

lint:
	black --check $(PYTHON_DIRS)
	isort --check $(PYTHON_DIRS)
	flake8 --max-line-length 88 --extend-ignore E203 $(PYTHON_DIRS)

# Scrape the TSA website
scrape:
	python scripts/00-scrape.py

# Run the data pipeline to transform and prep data for analysis
transform:
	python scripts/01-parse.py
	python scripts/02-combine.py
	python scripts/03-standardize.py
