import pytest

from src.store import Store


def test_store():
    s = Store()
    new = next(s)

    assert new.utp_code == "BirminghamAL"
    assert new.image_index == 230
