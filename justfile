default *ARGS:
    poetry run python -m src.annotator {{ARGS}}

scrape-img *ARGS:
    poetry run python -m src.scraper {{ARGS}}

export *ARGS:
    poetry run python -m src.export {{ARGS}}

test:
    poetry run pytest
