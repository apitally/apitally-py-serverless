.PHONY: format check test test-coverage

format:
	uv run ruff check apitally_serverless tests --fix --select I
	uv run ruff format apitally_serverless tests

check:
	uv run ruff check apitally_serverless tests
	uv run ruff format --diff apitally_serverless tests
	uv run mypy --install-types --non-interactive apitally_serverless tests

test:
	uv run pytest -v --tb=short

test-coverage:
	uv run pytest -v --tb=short --cov --cov-report=xml
