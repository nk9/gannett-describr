import json
import sqlite3

import pytest

from src.store import Store
from src.utils import (
    Source,
    buildImageList,
    missingSources,
    neededSources,
    parse_index_set,
)


def test_parse_index_set():
    assert parse_index_set("150-152,160,170-171") == [150, 151, 152, 160, 170, 171]


def test_parse_index_set_whitespace_and_overlap():
    assert parse_index_set(" 3-5, 4-6 ,") == [3, 4, 5, 6]


def test_parse_index_set_single_page_range():
    assert parse_index_set("7-7") == [7]


def test_parse_index_set_empty():
    assert parse_index_set("") == []


def test_parse_index_set_backwards():
    with pytest.raises(ValueError):
        parse_index_set("10-5")


def write_film(scrape_dir, film_no, count):
    films = scrape_dir / "films"
    films.mkdir(exist_ok=True)
    images = [
        f"https://www.familysearch.org/ark:/61903/3:1:{film_no}-{i:04}/image.xml"
        for i in range(count)
    ]
    (films / f"{film_no}.json").write_text(json.dumps({"images": images}))


@pytest.fixture
def map_csv(tmp_path):
    csv = tmp_path / "ed_map_nums.csv"
    csv.write_text(
        "year,utp_code,collection,digital_film_no,indexes\n"
        "1930,BostonMA,123,001,3-4\n"
        "1930,BostonMA,123,002,1\n"
        "1930,AkronOH,123,001,9-10\n"
        "1930,NoFilmOH,123,,1-2\n"
        "1930,MissingOH,123,003,1-2\n"
    )
    write_film(tmp_path, "001", 10)
    write_film(tmp_path, "002", 5)
    return csv


def test_needed_and_missing_sources(map_csv):
    assert neededSources(map_csv) == [
        Source("film", "001", "123"),
        Source("film", "002", "123"),
        Source("film", "003", "123"),
    ]
    assert missingSources(map_csv) == [Source("film", "003", "123")]


def test_build_image_list_from_index_sets(map_csv, tmp_path):
    images = buildImageList(map_csv, tmp_path / "img")

    assert [(i.utp_code, i.image_index) for i in images] == [
        ("BostonMA", 2),
        ("BostonMA", 3),
        ("BostonMA", 0),
        ("AkronOH", 8),
        ("AkronOH", 9),
    ]
    # Boston spans two films but is numbered as one metro
    assert [(i.metro_image_index, i.metro_image_count) for i in images[:3]] == [
        (0, 3),
        (1, 3),
        (2, 3),
    ]
    assert images[0].ark == "3:1:001-0002"
    assert images[0].local_path == tmp_path / "img" / "1930" / "BostonMA" / "001-0002.jpg"


def test_build_image_list_from_start_stop(tmp_path):
    csv = tmp_path / "ed_descr_nums.csv"
    csv.write_text(
        "year,utp_code,collection,digital_film_no,start_index,stop_index\n"
        "1930,BostonMA,123,001,4,6\n"
        "1930,AkronOH,123,001,9,9\n"
        "1930,SalemMA,123,001,,\n"
    )
    write_film(tmp_path, "001", 10)

    images = buildImageList(csv, tmp_path / "img")

    assert [(i.utp_code, i.image_index) for i in images] == [
        ("BostonMA", 4),
        ("BostonMA", 5),
        ("BostonMA", 6),
        ("AkronOH", 9),
    ]


def test_build_image_list_index_beyond_film(tmp_path):
    csv = tmp_path / "ed_map_nums.csv"
    csv.write_text(
        "year,utp_code,collection,digital_film_no,indexes\n" "1930,BostonMA,123,001,4-13\n"
    )
    write_film(tmp_path, "001", 5)

    images = buildImageList(csv, tmp_path / "img")

    assert [i.image_index for i in images] == [3, 4]


def test_init_db_creates_view_and_trigger():
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    Store(cursor, [])

    names = cursor.execute("SELECT type, name FROM sqlite_master").fetchall()
    assert ("view", "overview") in names
    assert ("trigger", "set_created_at") in names

    cursor.execute(
        "INSERT INTO images (year, utp_code, ark, image_index, cat) "
        "VALUES (1930, 'BostonMA', 'a', 1, 1)"
    )
    cursor.execute("INSERT INTO eds (image_id, name, created_at) VALUES (1, '1', NULL)")
    row = cursor.execute("SELECT utp_code, name, created_at FROM overview").fetchone()

    assert row[:2] == ("BostonMA", "1")
    assert row[2] is not None


def test_build_image_list_from_rolls(tmp_path):
    csv = tmp_path / "ed_map_nums.csv"
    csv.write_text(
        "year,utp_code,collection,roll_no,indexes\n"
        "1930,BirminghamAL,2329948,01,2-3\n"
        "1930,MobileAL,2329948,1,5\n"
        "1930,PhoenixAZ,2329948,2,1\n"
    )
    films = tmp_path / "films"
    films.mkdir()
    (films / "2329948-roll1.json").write_text(
        json.dumps(
            {
                "waypoint": "92V7-16N:1077255501",
                "images": [
                    f"https://www.familysearch.org/ark:/61903/3:1:ROLL1-{i}" for i in range(5)
                ],
            }
        )
    )

    assert neededSources(csv) == [
        Source("roll", "1", "2329948"),
        Source("roll", "2", "2329948"),
    ]
    assert missingSources(csv) == [Source("roll", "2", "2329948")]

    images = buildImageList(csv, tmp_path / "img")

    assert [(i.utp_code, i.image_index, i.ark) for i in images] == [
        ("BirminghamAL", 1, "3:1:ROLL1-1"),
        ("BirminghamAL", 2, "3:1:ROLL1-2"),
        ("MobileAL", 4, "3:1:ROLL1-4"),
    ]
    assert images[0].url == (
        "https://www.familysearch.org/ark:/61903/3:1:ROLL1-1"
        "?wc=92V7-16N%3A1077255501&cc=2329948&i=1"
    )


def test_indexes_column_is_one_based(tmp_path):
    csv = tmp_path / "ed_map_nums.csv"
    csv.write_text(
        "year,utp_code,collection,digital_film_no,indexes\n"
        "1930,BostonMA,123,001,1\n"
        "1930,AkronOH,123,001,0-2\n"
    )
    write_film(tmp_path, "001", 5)

    images = buildImageList(csv, tmp_path / "img")

    # Image 1 in the viewer is position 0; the row containing 0 is rejected
    assert [(i.utp_code, i.image_index, i.ark) for i in images] == [
        ("BostonMA", 0, "3:1:001-0000")
    ]
