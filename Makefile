.PHONY: generate check

generate:
	python3 scripts/generate_readme.py

check:
	python3 scripts/generate_readme.py --check
