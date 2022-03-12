import curses
import re
import typing

StrAttrFormatValues = typing.Dict[
    str,
    typing.Tuple[str, int]
]

class StrAttrFormat:
    """
    String attribute formatter used to apply curses attributes in a formatted string
    """
    FORMAT_REGEX = re.compile(r'{([^{}]+)}')

    def __init__(self,
        fmt: str,
        values: StrAttrFormatValues,
        default_attr: int = curses.A_NORMAL
    ):
        self.format: str = fmt
        self.values: StrAttrFormatValues = values
        self.default_attr: int = default_attr

    def copy(self):
        return StrAttrFormat(self.format, self.values, self.default_attr)

    def add(self, saf: typing.Union['StrAttrFormat', str]) -> 'StrAttrFormat':
        if isinstance(saf, StrAttrFormat):
            if self.default_attr != saf.default_attr:
                raise ValueError('default attributes do not match')

            intersection = set(self.values.keys()).intersection(set(saf.values.keys()))
            if len(intersection) != 0:
                raise ValueError(f'values are already defined: {intersection}')

            self.format += saf.format
            self.values.update(saf.values)
        else:
            self.format += saf

        return self

    def __add__(self, saf: typing.Union['StrAttrFormat', str]) -> 'StrAttrFormat':
        return self.copy().add(saf)

    def __iadd__(self, saf: typing.Union['StrAttrFormat', str]) -> 'StrAttrFormat':
        return self.add(saf)

    def __iter__(self) -> typing.Iterator[typing.Tuple[str, int]]:
        last_idx = 0
        for match in StrAttrFormat.FORMAT_REGEX.finditer(self.format):
            if last_idx < match.start():
                yield (self.format[last_idx:match.start()], self.default_attr)

            val, attr = self.values[match.groups()[0]]
            yield (val, attr)
            last_idx = match.end()
        if last_idx < len(self.format):
            yield (self.format[last_idx:], self.default_attr)

    def __str__(self) -> str:
        return ''.join(val for val, attr in self)

    def __len__(self) -> int:
        return len(str(self))

def addstrattrfmt(win: curses.window, y: int, x: int, saf: StrAttrFormat) -> int:
    return addstrlist(win, y, x, saf)

def addnstrattrfmt(win: curses.window, y: int, x: int, saf: StrAttrFormat, n: int) -> int:
    return addnstrlist(win, y, x, saf, n)

def addstrlist(
    win: curses.window,
    y: int,
    x: int,
    strings: typing.Iterable[typing.Tuple[str, int]]
) -> int:
    return addnstrlist(win, y, x, strings, sum(len(r) for r, _ in strings))

def addnstrlist(
    win: curses.window,
    y: int,
    x: int,
    strings: typing.Iterable[typing.Tuple[str, int]],
    n: int
) -> int:
    total_length = 0
    for string, attr in strings:
        if total_length + len(string) > n:
            win.addnstr(y, x + total_length, string, n - total_length, attr)
            total_length = n
            break

        win.addstr(y, x + total_length, string, attr)
        total_length += len(string)

    return total_length
