PYTHON ?= python3

.PHONY: test test-contracts test-unit check-openapi

test: test-contracts test-unit

test-contracts:
	$(PYTHON) -m unittest discover -s tests/contracts -p 'test_*.py'

test-unit:
	PYTHONPATH=apps/api $(PYTHON) -m unittest discover -s tests/unit -p 'test_*.py'

check-openapi:
	$(PYTHON) scripts/check_openapi.py
