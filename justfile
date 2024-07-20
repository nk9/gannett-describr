default:
    poetry run python -m src.annotator

scrape-img:
    poetry run python -m src.scraper

test:
    poetry run pytest
