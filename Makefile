PYTHON ?= python3

.PHONY: test test-contracts test-unit check-openapi db-upgrade db-downgrade db-history

test: test-contracts test-unit

test-contracts:
	$(PYTHON) -m unittest discover -s tests/contracts -p 'test_*.py'

test-unit:
	PYTHONPATH=apps/api $(PYTHON) -m unittest discover -s tests/unit -p 'test_*.py'

check-openapi:
	$(PYTHON) scripts/check_openapi.py

db-upgrade:
	$(PYTHON) -m alembic -c apps/api/alembic.ini upgrade head

db-downgrade:
	$(PYTHON) -m alembic -c apps/api/alembic.ini downgrade -1

db-history:
	$(PYTHON) -m alembic -c apps/api/alembic.ini history
