# On Windows without make: python scripts/tasks.py <task>
PY ?= python

.PHONY: dev seed test lint e2e data deploy destroy budget scheduler-pause scheduler-resume
dev seed test lint e2e data deploy destroy budget scheduler-pause scheduler-resume:
	$(PY) scripts/tasks.py $@
