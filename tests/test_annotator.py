from src.annotator import wrap_after


def test_wrap_after_fits():
    assert wrap_after("EDs: ", ["1", "2", "3A"], 20) == ["EDs: 1 2 3A"]


def test_wrap_after_empty():
    assert wrap_after("EDs: ", [], 20) == ["EDs: "]


def test_wrap_after_aligns_under_prefix():
    eds = [str(n) for n in range(1, 13)]

    assert wrap_after("EDs (12): ", eds, 20) == [
        "EDs (12): 1 2 3 4 5",
        "          6 7 8 9 10",
        "          11 12",
    ]


def test_wrap_after_never_splits_an_ed():
    assert wrap_after("> ", ["1234567890A", "2"], 12) == ["> 1234567890A", "  2"]
