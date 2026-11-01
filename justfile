desc_db := "../gannett-data/annotated.db"
desc_csv := "../gannett-data/scrape_fs/ed_descr_nums.csv"
desc_img := "../ed-desc-img"

map_db := "ed_maps.db"
map_csv := "../gannett-data/scrape_fs/ed_map_nums.csv"
map_img := "../ed-map-img"

default *ARGS:
    poetry run python -m src.annotator --db {{desc_db}} --index-csv {{desc_csv}} --img-dir {{desc_img}} {{ARGS}}

maps *ARGS:
    poetry run python -m src.annotator --db {{map_db}} --index-csv {{map_csv}} --img-dir {{map_img}} {{ARGS}}

off *ARGS:
    just default --offline {{ARGS}}

scrape-img *ARGS:
    poetry run python -m src.scraper --index-csv {{desc_csv}} --img-dir {{desc_img}} {{ARGS}}

scrape-maps *ARGS:
    poetry run python -m src.scraper --index-csv {{map_csv}} --img-dir {{map_img}} {{ARGS}}

export *ARGS:
    poetry run python -m src.export --db {{desc_db}} --out ../gannett-data/fs_ed_descriptions.parquet {{ARGS}}

export-maps *ARGS:
    poetry run python -m src.export --db {{map_db}} --out ../gannett-data/fs_ed_maps.parquet {{ARGS}}

test:
    poetry run pytest
