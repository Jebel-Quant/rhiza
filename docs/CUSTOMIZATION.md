# Customization Guide

This guide covers advanced customization options for Rhiza-based projects.

## 🛠️ Makefile Hooks & Extensions

Rhiza uses a modular Makefile system with extension points (hooks) that let you customize workflows without modifying core files.

### Available Hooks

You can hook into standard workflows using double-colon syntax (`::`) in `.rhiza/make.d/` files:

- `pre-install / post-install` - Runs around `make install`
- `pre-sync / post-sync` - Runs around repository synchronization
- `pre-validate / post-validate` - Runs around validation checks
- `pre-release / post-release` - Runs around release process
- `pre-bump / post-bump` - Runs around version bumping

### Example: Installing System Dependencies

Create `.rhiza/make.d/20-dependencies.mk`:

```makefile
pre-install::
	@if ! command -v dot >/dev/null 2>&1; then \
		echo "Installing graphviz..."; \
		sudo apt-get update && sudo apt-get install -y graphviz; \
	fi
```

This hook runs automatically before `make install`, ensuring graphviz is available.

### Example: Post-Release Tasks

Create `.rhiza/make.d/90-hooks.mk`:

```makefile
post-release::
	@echo "Running post-release tasks..."
	@./scripts/notify-team.sh
	@./scripts/update-changelog.sh
```

This runs automatically after `make release` completes.

### Example: Custom Build Steps

Create `.rhiza/make.d/50-custom.mk`:

```makefile
post-install::
	@echo "Installing specialized dependencies..."
	@uv pip install some-private-lib
	
##@ Custom Tasks
train-model: ## Train the ML model
	@uv run python scripts/train.py
```

### Ordering

Files in `.rhiza/make.d/` are loaded alphabetically. Use numeric prefixes to control order:

- `00-19`: Configuration & Variables
- `20-79`: Custom Tasks & Rules
- `80-99`: Hooks & Lifecycle logic

### Excluding from Template Updates

If you add custom `.mk` files, add them to the exclude list in your `.rhiza/template.yml`:

```yaml
exclude: |
  .rhiza/make.d/20-dependencies.mk
  .rhiza/make.d/90-hooks.mk
```

## 🔒 CodeQL Configuration

The CodeQL workflow (`.github/workflows/rhiza_codeql.yml`) performs security analysis on your code. However, **CodeQL requires GitHub Advanced Security**, which is:

- ✅ **Available for free** on public repositories
- ⚠️ **Requires GitHub Enterprise license** for private repositories

### Automatic Behavior

By default, the CodeQL workflow:
- **Runs automatically** on public repositories
- **Skips automatically** on private repositories (unless you have Advanced Security)

### Controlling CodeQL

You can override the default behavior using a repository variable:

1. Go to your repository → **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Create a new repository variable named `CODEQL_ENABLED`
3. Set the value:
   - `true` - Force CodeQL to run (use if you have Advanced Security on a private repo)
   - `false` - Disable CodeQL entirely (e.g., if it's causing issues)

### For Private Repositories with Advanced Security

If you have a GitHub Enterprise license with Advanced Security enabled:

```bash
# Enable CodeQL for your private repository
gh variable set CODEQL_ENABLED --body "true"
```

### For Users Without Advanced Security

No action needed! The workflow will automatically skip for private repositories. If you want to completely disable it:

```bash
# Disable CodeQL workflow
gh variable set CODEQL_ENABLED --body "false"
```

Or delete the workflow file:

```bash
# Remove CodeQL workflow
git rm .github/workflows/rhiza_codeql.yml
git commit -m "Remove CodeQL workflow"
```

## ⚙️ Configuration Variables

You can configure certain aspects of the Makefile by overriding variables. These can be set in your main `Makefile`, a `local.mk` file (for local developer overrides), or passed as environment variables / command-line arguments.

### Global Configuration

Add these to your `Makefile` or `local.mk` to make them persistent for the project or your environment:

```makefile
# Override default Python version
PYTHON_VERSION = 3.12

# Override test coverage threshold (default: 90)
COVERAGE_FAIL_UNDER = 80
```

### On-Demand Configuration

You can also pass variables directly to `make` for one-off commands:

```bash
# Run tests requiring only 80% coverage
make test COVERAGE_FAIL_UNDER=80
```

## 🎨 Documentation Customization

You can customize the API documentation and companion book.

### Project Logo

The API documentation includes a logo in the sidebar. You can override the default logo (`assets/rhiza-logo.svg`) by setting the `LOGO_FILE` variable in your Makefile or `local.mk`:

```makefile
LOGO_FILE := assets/my-custom-logo.png
```

### Custom Templates

You can customize the look and feel of the API documentation by providing your own Jinja2 templates.
Place your custom templates in the `book/pdoc-templates` directory.

For example, to override the main module template, create `book/pdoc-templates/module.html.jinja2`.

See the [pdoc documentation on templates](https://pdoc.dev/docs/pdoc.html#edit-pdocs-html-template) for full details on how to override specific parts of the documentation.

For more details on customizing the documentation, see [book/README.md](../book/README.md).

## 📖 Complete Documentation

For detailed information about extending and customizing the Makefile system, see [.rhiza/make.d/README.md](../.rhiza/make.d/README.md).

---

## 🧩 Customization Recipes

Common customization patterns for real-world scenarios.

### Recipe 1: Multi-Environment Configuration

**Scenario:** Different settings for dev, staging, and production.

**Solution:**

Create `.rhiza/make.d/30-environments.mk`:

```makefile
# Environment selection
ENV ?= dev

##@ Environment Management

.PHONY: deploy-dev
deploy-dev: ## Deploy to development
	@$(MAKE) deploy ENV=dev

.PHONY: deploy-staging  
deploy-staging: ## Deploy to staging
	@$(MAKE) deploy ENV=staging

.PHONY: deploy-prod
deploy-prod: ## Deploy to production
	@$(MAKE) deploy ENV=prod

.PHONY: deploy
deploy: ## Deploy to selected environment (ENV=dev|staging|prod)
	@echo "Deploying to $(ENV)..."
	@./scripts/deploy.sh $(ENV)
```

**Usage:**

```bash
make deploy-dev       # Deploy to dev
make deploy ENV=prod  # Deploy to prod
```

---

### Recipe 2: Database Migrations

**Scenario:** Run database migrations as part of your workflow.

**Solution:**

Create `.rhiza/make.d/40-database.mk`:

```makefile
DB_URL ?= postgresql://localhost/mydb

##@ Database

.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "Running migrations..."
	@uv run alembic upgrade head

.PHONY: db-rollback
db-rollback: ## Rollback last migration
	@echo "Rolling back..."
	@uv run alembic downgrade -1

.PHONY: db-reset
db-reset: ## Reset database (WARNING: destructive)
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		uv run alembic downgrade base; \
		uv run alembic upgrade head; \
	fi

# Hook: Run migrations after install
post-install::
	@echo "Running database migrations..."
	@$(MAKE) db-migrate
```

---

### Recipe 3: Docker Integration

**Scenario:** Build and run Docker containers as part of development.

**Solution:**

Create `.rhiza/make.d/45-docker.mk`:

```makefile
DOCKER_IMAGE ?= myapp
DOCKER_TAG ?= latest

##@ Docker

.PHONY: docker-build
docker-build: ## Build Docker image
	@docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) -f docker/Dockerfile .

.PHONY: docker-run
docker-run: ## Run Docker container
	@docker run -p 8000:8000 $(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: docker-shell
docker-shell: ## Open shell in Docker container
	@docker run -it $(DOCKER_IMAGE):$(DOCKER_TAG) /bin/bash

.PHONY: docker-push
docker-push: docker-build ## Build and push to registry
	@docker push $(DOCKER_IMAGE):$(DOCKER_TAG)

# Hook: Build Docker image before release
pre-release::
	@echo "Building Docker image..."
	@$(MAKE) docker-build DOCKER_TAG=$(VERSION)
```

---

### Recipe 4: Code Generation

**Scenario:** Auto-generate code from schemas or templates.

**Solution:**

Create `.rhiza/make.d/35-codegen.mk`:

```makefile
##@ Code Generation

.PHONY: codegen
codegen: ## Generate code from schemas
	@echo "Generating code..."
	@uv run python scripts/generate_models.py
	@uv run python scripts/generate_api.py
	@$(MAKE) fmt  # Format generated code

.PHONY: codegen-check
codegen-check: ## Check if generated code is up to date
	@echo "Checking generated code..."
	@git diff --quiet generated/ || (echo "ERROR: Generated code out of date. Run 'make codegen'" && exit 1)

# Hook: Generate code before tests
pre-test::
	@$(MAKE) codegen-check
```

---

### Recipe 5: Custom Linting Rules

**Scenario:** Add project-specific linting beyond ruff.

**Solution:**

Create `.rhiza/make.d/55-lint.mk`:

```makefile
##@ Additional Linting

.PHONY: lint-custom
lint-custom: ## Run custom project linters
	@echo "Running custom linters..."
	@uv run python scripts/check_naming_conventions.py
	@uv run python scripts/check_import_order.py
	@uv run python scripts/check_docstrings.py

.PHONY: lint-all
lint-all: fmt lint-custom ## Run all linting (ruff + custom)
	@echo "✓ All linting passed"

# Hook: Run custom linting with validate
post-validate::
	@$(MAKE) lint-custom
```

---

### Recipe 6: Machine Learning Workflows

**Scenario:** Train, evaluate, and deploy ML models.

**Solution:**

Create `.rhiza/make.d/60-ml.mk`:

```makefile
MODEL_PATH ?= models/current.pkl
DATA_PATH ?= data/training.csv

##@ Machine Learning

.PHONY: ml-train
ml-train: ## Train ML model
	@echo "Training model..."
	@uv run python scripts/train.py --data $(DATA_PATH) --output $(MODEL_PATH)

.PHONY: ml-evaluate
ml-evaluate: ## Evaluate model performance
	@echo "Evaluating model..."
	@uv run python scripts/evaluate.py --model $(MODEL_PATH)

.PHONY: ml-serve
ml-serve: ## Start model serving API
	@echo "Starting model server..."
	@uv run uvicorn app.main:app --reload

.PHONY: ml-experiment
ml-experiment: ## Run ML experiment tracking
	@echo "Running experiment..."
	@uv run python scripts/experiment.py --track

# Hook: Validate model before release
pre-release::
	@$(MAKE) ml-evaluate
```

---

### Recipe 7: Data Pipeline

**Scenario:** ETL pipeline for data processing.

**Solution:**

Create `.rhiza/make.d/65-data.mk`:

```makefile
##@ Data Pipeline

.PHONY: data-extract
data-extract: ## Extract data from sources
	@echo "Extracting data..."
	@uv run python scripts/extract.py

.PHONY: data-transform
data-transform: ## Transform extracted data
	@echo "Transforming data..."
	@uv run python scripts/transform.py

.PHONY: data-load
data-load: ## Load data to destination
	@echo "Loading data..."
	@uv run python scripts/load.py

.PHONY: data-pipeline
data-pipeline: data-extract data-transform data-load ## Run full ETL pipeline
	@echo "✓ Pipeline complete"

.PHONY: data-validate
data-validate: ## Validate data quality
	@uv run python scripts/validate_data.py
```

---

### Recipe 8: API Client Generation

**Scenario:** Generate API clients from OpenAPI/Swagger specs.

**Solution:**

Create `.rhiza/make.d/38-api-client.mk`:

```makefile
API_SPEC ?= openapi.yaml
CLIENT_DIR ?= generated/client

##@ API Client

.PHONY: api-generate
api-generate: ## Generate API client from spec
	@echo "Generating API client..."
	@uv run openapi-python-client generate --path $(API_SPEC) --output-path $(CLIENT_DIR)
	@$(MAKE) fmt

.PHONY: api-update
api-update: ## Update existing API client
	@echo "Updating API client..."
	@uv run openapi-python-client update --path $(API_SPEC) --output-path $(CLIENT_DIR)
	@$(MAKE) fmt

.PHONY: api-validate
api-validate: ## Validate OpenAPI spec
	@uv run openapi-spec-validator $(API_SPEC)
```

---

### Recipe 9: Notification Hooks

**Scenario:** Send notifications on certain events.

**Solution:**

Create `.rhiza/make.d/85-notifications.mk`:

```makefile
SLACK_WEBHOOK ?= $(shell echo $$SLACK_WEBHOOK)

##@ Notifications

.PHONY: notify-slack
notify-slack: ## Send Slack notification (MESSAGE=...)
	@if [ -n "$(SLACK_WEBHOOK)" ]; then \
		curl -X POST -H 'Content-type: application/json' \
		--data '{"text":"$(MESSAGE)"}' \
		$(SLACK_WEBHOOK); \
	fi

# Hook: Notify on successful release
post-release::
	@$(MAKE) notify-slack MESSAGE="🚀 Released version $(VERSION)"

# Hook: Notify on test failures
post-test::
	@if [ $$? -ne 0 ]; then \
		$(MAKE) notify-slack MESSAGE="❌ Tests failed on branch $(shell git rev-parse --abbrev-ref HEAD)"; \
	fi
```

---

### Recipe 10: Performance Monitoring

**Scenario:** Track performance metrics over time.

**Solution:**

Create `.rhiza/make.d/70-performance.mk`:

```makefile
PERF_LOG ?= .performance.log

##@ Performance

.PHONY: perf-profile
perf-profile: ## Profile application performance
	@echo "Profiling..."
	@uv run python -m cProfile -o profile.stats scripts/run.py
	@uv run python -m pstats profile.stats

.PHONY: perf-memory
perf-memory: ## Profile memory usage
	@echo "Memory profiling..."
	@uv run python -m memory_profiler scripts/run.py

.PHONY: perf-track
perf-track: ## Track performance metrics
	@echo "Tracking performance..."
	@echo "$(shell date): $(shell uv run python scripts/measure_perf.py)" >> $(PERF_LOG)

# Hook: Track performance on each test run
post-test::
	@$(MAKE) perf-track
```

---

## 🎯 Real-World Use Cases

### Use Case 1: Monorepo with Multiple Packages

**Challenge:** Manage multiple Python packages in one repository.

**Solution:**

```makefile
# .rhiza/make.d/25-monorepo.mk
PACKAGES := package1 package2 package3

##@ Monorepo

.PHONY: test-all-packages
test-all-packages: ## Test all packages
	@for pkg in $(PACKAGES); do \
		echo "Testing $$pkg..."; \
		cd $$pkg && uv run pytest || exit 1; \
	done

.PHONY: build-all-packages
build-all-packages: ## Build all packages
	@for pkg in $(PACKAGES); do \
		echo "Building $$pkg..."; \
		cd $$pkg && uv build || exit 1; \
	done
```

---

### Use Case 2: Microservices Orchestration

**Challenge:** Coordinate multiple services locally.

**Solution:**

```makefile
# .rhiza/make.d/48-services.mk
SERVICES := auth api worker

##@ Services

.PHONY: services-up
services-up: ## Start all services
	@docker-compose up -d

.PHONY: services-down
services-down: ## Stop all services
	@docker-compose down

.PHONY: services-logs
services-logs: ## View service logs
	@docker-compose logs -f

.PHONY: service-restart
service-restart: ## Restart a service (SERVICE=...)
	@docker-compose restart $(SERVICE)
```

---

### Use Case 3: Third-Party Tool Integration

**Challenge:** Integrate tools like Terraform, Ansible, etc.

**Solution:**

```makefile
# .rhiza/make.d/75-infra.mk
TERRAFORM_DIR := infrastructure
ANSIBLE_PLAYBOOK := deploy.yml

##@ Infrastructure

.PHONY: infra-plan
infra-plan: ## Plan infrastructure changes
	@cd $(TERRAFORM_DIR) && terraform plan

.PHONY: infra-apply
infra-apply: ## Apply infrastructure changes
	@cd $(TERRAFORM_DIR) && terraform apply

.PHONY: config-deploy
config-deploy: ## Deploy configuration with Ansible
	@ansible-playbook $(ANSIBLE_PLAYBOOK)
```

---

## 📝 Customization Best Practices

### 1. Use Descriptive Names

```makefile
# Good
.PHONY: deploy-to-production
deploy-to-production: ## Deploy to production environment

# Bad
.PHONY: dtp
dtp: ## ???
```

### 2. Add Help Text

Always include `## description` for custom targets:

```makefile
.PHONY: custom-task
custom-task: ## This appears in 'make help'
	@echo "Running custom task"
```

### 3. Use Variables for Configuration

```makefile
# Good
API_URL ?= https://api.example.com
deploy:
	@curl $(API_URL)/deploy

# Bad (hardcoded)
deploy:
	@curl https://api.example.com/deploy
```

### 4. Fail Fast

```makefile
# Good - stops on error
test: unit-tests integration-tests

# Bad - continues after failure
test:
	-$(MAKE) unit-tests
	-$(MAKE) integration-tests
```

### 5. Document Dependencies

```makefile
# Good - clear prerequisites
deploy: build test validate
	@./scripts/deploy.sh

# Bad - hidden dependencies
deploy:
	@./scripts/deploy.sh  # What needs to run first?
```

---

## 🔧 Advanced Techniques

### Conditional Execution

```makefile
.PHONY: maybe-deploy
maybe-deploy:
	@if [ "$(BRANCH)" = "main" ]; then \
		$(MAKE) deploy; \
	else \
		echo "Skipping deploy on $(BRANCH)"; \
	fi
```

### Parallel Execution

```makefile
.PHONY: parallel-tests
parallel-tests:
	@$(MAKE) -j4 test-unit test-integration test-e2e test-performance
```

### Dynamic Targets

```makefile
# Generate targets for each service
define SERVICE_TEMPLATE
.PHONY: test-$(1)
test-$(1): ## Test $(1) service
	@cd services/$(1) && uv run pytest
endef

$(foreach service,$(SERVICES),$(eval $(call SERVICE_TEMPLATE,$(service))))
```

---

## 📚 Related Documentation

- [Workflows](WORKFLOWS.md) — Development workflows
- [Architecture](ARCHITECTURE.md) — System architecture
- [CI/CD](ci-cd.md) — Continuous integration
- [FAQ](faq.md) — Frequently asked questions
