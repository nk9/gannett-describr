default *ARGS:
    poetry run python -m src.annotator {{ARGS}}

off *ARGS:
    poetry run python -m src.annotator --offline {{ARGS}}

scrape-img *ARGS:
    poetry run python -m src.scraper {{ARGS}}

export *ARGS:
    poetry run python -m src.export {{ARGS}}

test:
    poetry run pytest
