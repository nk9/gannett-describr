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

    def __eq__(self, other):
        if not isinstance(other, Ed):
            return NotImplemented

        return self.num == other.num and self.suff == other.suff

    def __lt__(self, other):
        if not isinstance(other, Ed):
            return NotImplemented

        return self.num < other.num or (
            self.num == other.num and self.suff < other.suff
        )

    @classmethod
    def from_str(cls, s):
        if len(s):
            tail = s.lstrip("0123456789")
            head = s[: len(s) - len(tail)]

            if head.isdigit():
                return cls(int(head), tail)

        return None


class ManualEDList:
    def __init__(self):
        self.reset()

    def reset(self):
        self.index = None
        self.list = []

    def next(self):
        if len(self.list):
            # if self.index + 1 == len(self.list):
            #     # wrap around
            #     self.index = 0
            # else:
            self.index = (self.index + 1) % len(self.list)

    def prev(self):
        if len(self.list):
            if self.index - 1 < 0:
                # wrap around
                self.index = len(self.list) - 1
            else:
                self.index = (self.index - 1) % len(self.list)

    def addSlot(self, manual_ed):
        new = Ed.from_str(manual_ed)

        if new is not None:
            self.list.append(new)
            self.index = len(self.list) - 1

        return new

    def incrementCurr(self):
        ed = self.curr()

        if ed is not None:
            ed += 1
            self.list[self.index] = ed

        return ed

    def decrementCurr(self):
        ed = self.curr()

        if ed is not None:
            ed -= 1
            self.list[self.index] = ed

        return ed

    def curr(self):
        if self.index is None or len(self.list) == 0:
            return None

        return self.list[self.index]

    def removeCurr(self):
        del self.list[self.index]

        if self.index >= len(self.list):
            if len(self.list) == 0:
                self.index = None
            else:
                self.index -= 1

    @property
    def currStr(self):
        curr = self.curr()

        if curr is None:
            return '""'

        return str(curr)
