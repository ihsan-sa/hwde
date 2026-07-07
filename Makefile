# POSIX entry points (CI / Linux / macOS). This Windows host has no make:
# use check.cmd, which runs the same steps.
PY ?= .venv/bin/python

check:
	$(PY) -m pytest
	$(PY) .claude/skills/ai-ee/scripts/check_env.py --quiet > /dev/null

env:
	$(PY) .claude/skills/ai-ee/scripts/check_env.py --full

.PHONY: check env
