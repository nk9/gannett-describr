class Ed:
    def __init__(self, num: int, suff=""):
        self.num = num
        self.suff = suff.upper()

    def __repr__(self):
        return f"{self.num}{self.suff}"

    def __iadd__(self, other: int):
        self.num += other
        return self

    def __isub__(self, other: int):
        if self.num > 1:
            self.num -= other

        return self

    @classmethod
    def from_str(cls, s):
        tail = s.lstrip("0123456789")
        head = s[: len(s) - len(tail)]

        if head.isdigit():
            return cls(int(head), tail)

        return None
