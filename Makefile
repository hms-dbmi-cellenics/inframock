#!make
#----------------------------------------
# Settings
#----------------------------------------
.DEFAULT_GOAL := help
#--------------------------------------------------
# Variables
#--------------------------------------------------
PYTHON_FILES?=$$(find python -name '*.py')
#--------------------------------------------------
# Targets
#--------------------------------------------------
bootstrap: ## Installs requirements (python linter & formatter)
	@pip install flake8 black
fmt: ## Formats python files
	@echo "==> Formatting files..."
	@black $(PYTHON_FILES)
	@echo ""
check: ## Checks code for linting/construct errors
	@echo "==> Checking if files are well formatted..."
	@flake8 $(PYTHON_FILES)
	@echo "    [✓]\n"
build: ## Builds the docker-compose environment
	@echo "==> Building docker image..."
	@docker-compose build
	@echo "    [✓]\n"
run: ## Runs the docker environment
	@docker-compose up
reload-data: ## Reloads the input data found in ./data. NOTE: it will not remove from s3 & dynamo generated data like processed matrices, or plots. If you need a clean start, stop & re-run inframock.
	@docker-compose  up -d --no-deps --build service
.PHONY: bootstrap fmt check build run clean help
clean: ## Cleans up temporary files
	@echo "==> Cleaning up ..."
	@find . -name "*.pyc" -exec rm -f {} \;
	@echo "    [✓]"
	@echo ""
help: ## Shows available targets
	@fgrep -h "## " $(MAKEFILE_LIST) | fgrep -v fgrep | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-13s\033[0m %s\n", $$1, $$2}'
