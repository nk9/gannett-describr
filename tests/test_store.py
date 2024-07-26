import sqlite3

import pytest
from src.store import Image, Store, prev
from src.ed import Ed


@pytest.fixture
def test_db():
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()

    yield cursor

    connection.close()


def test_store_init(test_db, manyUtps):
    s = Store(test_db, manyUtps)
    s.populate_db()

    old = s.curr()

    assert old.utp_code == "BirminghamAL"
    assert old.image_index == 229

    new = next(s)

    assert new.utp_code == "BirminghamAL"
    assert new.image_index == 230

    now = prev(s)

    assert now.utp_code == "BirminghamAL"
    assert now.image_index == 229


def test_across_utp_boundary(test_db, manyUtps):
    s = Store(test_db, manyUtps)
    s.populate_db()

    old = s.curr()

    for _ in range(3):
        new = next(s)

    assert old != new
    assert old.utp_code != new.utp_code


def test_next_metro(test_db, manyUtps):
    s = Store(test_db, manyUtps)
    s.populate_db()

    img = s.nextMetro()
    assert img.ark == manyUtps[3].ark
    img = s.nextMetro()
    assert img.ark == manyUtps[5].ark
    img = s.nextMetro()
    assert img.ark == manyUtps[8].ark

    s.nextMetro() == None


def test_prev_metro(test_db, manyUtps):
    s = Store(test_db, manyUtps)
    s.populate_db()

    s.index = 8

    img = s.prevMetro()
    assert img.ark == manyUtps[7].ark
    img = s.prevMetro()
    assert img.ark == manyUtps[4].ark
    img = s.prevMetro()
    assert img.ark == manyUtps[2].ark

    s.prevMetro() == None


def test_image_add_ed(oneImage):
    oneImage.addED(1)
    oneImage.addED(2)
    oneImage.addED(2)
    oneImage.addED("3a")

    assert list(oneImage.eds) == ["1", "2", "3A"]


def test_remove_ed(oneImage):
    oneImage.addED(1)
    oneImage.removeED(1)
    oneImage.addED("None")
    oneImage.removeED("None")

    assert len(oneImage.eds) == 0


def test_image_url(oneImage):
    assert (
        oneImage.url
        == "https://www.familysearch.org/ark:/61903/3:1:3Q9M-CSVR-VSRX-L?i=229&cat=1037259"
    )


def test_skip_to_last_entered(test_db, manyUtps):
    s = Store(test_db, manyUtps)
    s.populate_db()
    s.images[2].eds.update(["4A", "4B"])
    s.skipToLastEntered()

    cur = s.curr()

    assert cur.ark == manyUtps[2].ark


def test_largest_ed(test_db, oneImage):
    s = Store(test_db, [oneImage])
    s.populate_db()

    ed_name = s.largestEDForCurrentMetro()

    assert ed_name == "1"

    s.addEDToCurrentImage(Ed(10))

    ed_name = s.largestEDForCurrentMetro()

    assert ed_name == "10"


@pytest.fixture
def manyUtps():
    return [
        Image("1930", "BirminghamAL", "3:1:3Q9M-CSVR-VSRX-L", 229, 0, 3, "1037259"),
        Image("1930", "BirminghamAL", "3:1:3Q9M-CSVR-VSR4-H", 230, 1, 3, "1037259"),
        Image("1930", "BirminghamAL", "3:1:3Q9M-CSVR-VSTT-L", 231, 2, 3, "1037259"),
        Image("1930", "OaklandCA", "3:1:3QHV-R32D-G1N2", 15, 0, 2, "1037259"),
        Image("1930", "OaklandCA", "3:1:3QHV-532D-GTWB", 16, 1, 2, "1037259"),
        Image("1930", "SpringfieldMA", "3:1:3QHV-532D-G9FS-M", 316, 0, 3, "1037259"),
        Image("1930", "SpringfieldMA", "3:1:3QHV-R32D-G92N-3", 317, 1, 3, "1037259"),
        Image("1930", "SpringfieldMA", "3:1:3QHV-532D-G9XN-Z", 318, 2, 3, "1037259"),
        Image("1930", "BostonMA", "3:1:3QHV-532D-G98P-V", 757, 0, 1, "1037259"),
    ]


@pytest.fixture
def oneImage():
    return Image("1930", "BirminghamAL", "3:1:3Q9M-CSVR-VSRX-L", 229, 0, 1, "1037259")
