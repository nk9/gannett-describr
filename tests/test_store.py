import pytest

from src.store import Store, Image


def test_store_init(twoUtps):
    s = Store(twoUtps)
    old = s.curr()

    assert old.utp_code == "BirminghamAL"
    assert old.image_index == 229

    new = next(s)

    assert new.utp_code == "BirminghamAL"
    assert new.image_index == 230


def test_across_utp_boundary(twoUtps):
    s = Store(twoUtps)
    old = s.curr()

    for _ in range(3):
        new = next(s)

    assert old != new
    assert old.utp_code != new.utp_code


def test_image_add_ed(oneImage):
    oneImage.add(1)
    oneImage.add(2)
    oneImage.add(2)

    assert oneImage.eds == [1, 2]


def test_image_url(oneImage):
    assert (
        oneImage.url
        == "https://www.familysearch.org/ark:/61903/3:1:3Q9M-CSVR-VSRX-L?i=229&cat=1037259"
    )


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
