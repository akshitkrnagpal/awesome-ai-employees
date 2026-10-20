.PHONY: generate check icons

generate:
	python3 scripts/generate_readme.py

check:
	python3 scripts/generate_readme.py --check
	python3 -m unittest discover -s tests

icons:
	python3 scripts/fetch_company_icons.py
	python3 scripts/generate_readme.py
