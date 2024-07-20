default *ARGS:
    poetry run python -m src.annotator {{ARGS}}

scrape-img:
    poetry run python -m src.scraper

test:
    poetry run pytest
