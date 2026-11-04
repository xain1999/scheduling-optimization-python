# Companion code -- shortcuts for code/run.py (run from the repository root)
#   make test          quick examples and test suites
#   make examples      every other example script
#   make figures       regenerate the figures into figures/
#   make experiments   rerun all benchmarks (several hours)

PY ?= python3

.PHONY: test examples figures experiments

test:
	cd code && $(PY) run.py test

examples:
	cd code && $(PY) run.py examples

figures:
	cd code && $(PY) run.py figures

experiments:
	cd code && $(PY) run.py experiments
