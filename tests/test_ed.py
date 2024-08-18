import pytest
from src.ed import Ed, ManualEDList


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


def test_empty_str():
    e = Ed.from_str("")

    assert e is None


def test_eq():
    e1 = Ed.from_str("345")
    e2 = Ed.from_str("345")

    assert e1 == e2


def test_lt():
    e1 = Ed(1)
    e5 = Ed(5)
    e5a = Ed.from_str("5A")
    e5b = Ed.from_str("5B")

    assert e1 < e5
    assert e5 < e5a
    assert e5a < e5b


def test_ed_list():
    m = ManualEDList()
    m.addSlot("549")

    assert m.curr() == Ed.from_str("549")


def test_ed_list_increment():
    m = ManualEDList()
    m.addSlot("549")
    m.addSlot("123")

    assert m.curr() == Ed.from_str("123")

    m.next()

    assert m.curr() == Ed.from_str("549")


def test_ed_list_prev():
    m = ManualEDList()
    m.addSlot("123")
    m.addSlot("456")

    m.prev()
    m.prev()

    assert m.curr() == Ed.from_str("456")
