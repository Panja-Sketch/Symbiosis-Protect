# On Windows without make: python scripts/tasks.py <task>
PY ?= python

.PHONY: dev seed test lint deploy
dev seed test lint deploy:
	$(PY) scripts/tasks.py $@
