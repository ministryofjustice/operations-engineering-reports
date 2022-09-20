SHELL=bash

setup:
	python3 -m venv venv
	@venv/bin/pip3 install --upgrade pip
	@venv/bin/pip3 install -r requirements.txt

venv: requirements.txt requirements-test.txt
	python3 -m venv venv
	@venv/bin/pip3 install --upgrade pip
	@venv/bin/pip3 install -r requirements.txt
	@venv/bin/pip3 install -r requirements-test.txt

source_files = ./instance ./report_app ./tests ./dynambodb_testing setup.py operations_engineering_reports.py build.py
lint: venv
	@venv/bin/flake8 --ignore=E501,W503 $(source_files)
	@venv/bin/mypy --ignore-missing-imports $(source_files)
	@venv/bin/pylint --recursive=y $(source_files)

format: venv
	@venv/bin/black $(source_files)

clean-test:
	rm -fr venv
	rm -fr .tox/
	rm -fr .pytest_cache
	rm -fr .mypy_cache
	rm -fr .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

test: venv

all:

local:
	bash scripts/start-local.sh

prod: lint
	bash scripts/start-prod.sh

dev:
	bash scripts/start-dev.sh

stop:
	docker-compose down -v --remove-orphans

.PHONY: setup dev stop venv lint test format local prod clean-test all