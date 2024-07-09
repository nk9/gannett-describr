import sqlite3

import pytest
from src.store import Image, Store, prev


@pytest.fixture
def test_db():
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()

    yield cursor

    connection.close()


def test_store_init(test_db, twoUtps):
    s = Store(test_db, twoUtps)
    old = s.curr()

    assert old.utp_code == "BirminghamAL"
    assert old.image_index == 229

    new = next(s)

    assert new.utp_code == "BirminghamAL"
    assert new.image_index == 230

    now = prev(s)

    assert now.utp_code == "BirminghamAL"
    assert now.image_index == 229


def test_across_utp_boundary(test_db, twoUtps):
    s = Store(test_db, twoUtps)
    old = s.curr()

    for _ in range(3):
        new = next(s)

    assert old != new
    assert old.utp_code != new.utp_code


def test_image_add_ed(oneImage):
    oneImage.addED(1)
    oneImage.addED(2)
    oneImage.addED(2)
    oneImage.addED("3a")

    assert list(oneImage.eds) == ["1", "2", "3A"]


def test_image_url(oneImage):
    assert (
        oneImage.url
        == "https://www.familysearch.org/ark:/61903/3:1:3Q9M-CSVR-VSRX-L?i=229&cat=1037259"
    )


def test_skip_to_last_entered(test_db, twoUtps):
    s = Store(test_db, twoUtps)
    s.images[2].eds.update(["4A", "4B"])
    s.skipToLastEntered()

    cur = s.curr()

    assert cur.ark == twoUtps[2].ark


@pytest.fixture
def twoUtps():
    return [
        Image("1930", "BirminghamAL", "3:1:3Q9M-CSVR-VSRX-L", 229, "1037259"),
        Image("1930", "BirminghamAL", "3:1:3Q9M-CSVR-VSR4-H", 230, "1037259"),
        Image("1930", "BirminghamAL", "3:1:3Q9M-CSVR-VSTT-L", 231, "1037259"),
        Image("1930", "OaklandCA", "3:1:3QHV-R32D-G1N2", 15, "1037259"),
        Image("1930", "OaklandCA", "3:1:3QHV-532D-GTWB", 16, "1037259"),
    ]


@pytest.fixture
def oneImage():
    return Image("1930", "BirminghamAL", "3:1:3Q9M-CSVR-VSRX-L", 229, "1037259")
