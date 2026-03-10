.PHONY: build run run-s3 reset lint

build:
	python -m py_compile scraper.py

run:
	python scraper.py

run-s3:
	python scraper.py --s3-bucket "$${S3_BUCKET}" --s3-prefix "$${S3_PREFIX-sc-procurement}"

reset:
	python scraper.py --reset-baseline

lint:
	python -m py_compile scraper.py
