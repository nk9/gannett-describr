import pytest
from src.ed import Ed


def test_ed():
    e = Ed(1)

    assert e.num == 1
    assert e.suff == ""


def test_increment():
    e = Ed(1, "B")
    e += 1

    assert e.num == 2
    assert e.suff == "B"
    assert str(e) == "2B"


def test_from_str():
    e = Ed.from_str("7a")
    assert e.num == 7
    assert e.suff == "A"


def test_from_str_no_char():
    e = Ed.from_str("1")

    assert e.num == 1
    assert e.suff == ""
