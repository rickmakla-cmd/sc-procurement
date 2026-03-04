.PHONY: build run reset lint

build:
	python -m py_compile scraper.py

run:
	python scraper.py

reset:
	python scraper.py --reset-baseline

lint:
	python -m py_compile scraper.py
