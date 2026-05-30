
PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install test mutate mutate_fast htmlcov results clean

install:
	$(PIP) install -r requirements.txt

test:
	pytest -q

mutate:
	mutmut run

mutate_fast:
	mutmut run --since $(shell git merge-base main HEAD)

htmlcov:
	pytest --cov=billing --cov-branch --cov-report=html

results:
	mutmut results

clean:
	rm -rf .mutmut_cache htmlcov .coverage
