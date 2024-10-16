.ONESHELL:

# Default values for variables (can be overridden by passing arguments to `make`)
PYTHON_SOURCE_FILES = ./instance ./report_app ./tests ./dynambodb_testing setup.py operations_engineering_reports.py build.py
RELEASE_NAME ?= default-release-name
AUTH0_CLIENT_ID ?= default-auth0-client-id
AUTH0_CLIENT_SECRET ?= default-auth0-client-secret
APP_SECRET_KEY ?= default-app-secret-key
ENCRYPTION_KEY ?= default-encryption-key
API_KEY ?= default-api-key
HOST_SUFFIX ?= default-host-suffix
IMAGE ?= default-image
REGISTRY ?= default-registry

# Targets
help:
	@echo "Available commands:"
	@echo "make venv            - Setup the environment"
	@echo "make test             - Run tests"
	@echo "make deploy-dev       - Deploy the application to the dev namespace"


venv: 
	pip3 install pipenv
	pipenv install --dev 

lint: venv
	pipenv run flake8 --ignore=E501,W503 $(PYTHON_SOURCE_FILES)
	pipenv run mypy --ignore-missing-imports $(PYTHON_SOURCE_FILES)
	pipenv run pylint --recursive=y $(PYTHON_SOURCE_FILES)

format: venv
	pipenv run black $(PYTHON_SOURCE_FILES)

test:
	export FLASK_CONFIGURATION=development; python3 -m pytest -v

clean-test:
	pipenv --rm
	rm -fr .tox/
	rm -fr .pytest_cache
	rm -fr .mypy_cache
	rm -fr .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache


# To run locally, you need to pass the following:
# make deploy IMAGE=my-image RELEASE_NAME=my-release AUTH0_CLIENT_ID=my-auth0-id AUTH0_CLIENT_SECRET=my-secret APP_SECRET_KEY=my-app-secret ENCRYPTION_KEY=my-encryption-key API_KEY=my-api-key HOST_SUFFIX=my-host-suffix
deploy-dev:
	helm --debug upgrade $(RELEASE_NAME) helm/operations-engineering-reports \
		--install \
		--force \
		--wait \
		--set image.tag=$(IMAGE) \
		--set application.auth0ClientId=$(AUTH0_CLIENT_ID) \
		--set application.auth0ClientSecret=$(AUTH0_CLIENT_SECRET) \
		--set application.appSecretKey=$(APP_SECRET_KEY) \
		--set application.encryptionKey=$(ENCRYPTION_KEY) \
		--set application.apiKey=$(API_KEY) \
		--set ingress.hosts={operations-engineering-reports-dev-$(HOST_SUFFIX).cloud-platform.service.justice.gov.uk} \
		--set image.repository=754256621582.dkr.ecr.eu-west-2.amazonaws.com/operations-engineering/operations-engineering-reports-dev-ecr \
		--namespace operations-engineering-reports-dev

delete-dev:
	helm delete $(RELEASE_NAME) --namespace operations-engineering-reports-dev

all:

dev:
	bash scripts/start-db-dev.sh

db-ui:
	bash scripts/start-db-ui.sh

stop:
	docker-compose down -v --remove-orphans

.PHONY: dev stop venv lint test format local prod clean-test all
