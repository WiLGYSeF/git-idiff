import curses

class CursesPad:
    def __init__(self, window, **kwargs):
        self.height: int = kwargs['height']
        self.width: int = kwargs['width']
        self.offset_y: int = kwargs['offset_y']
        self.offset_x: int = kwargs['offset_x']

        self.pad = window.newpad(self.height, self.width)

        self._y: int = 0
        self._x: int = 0

    def scroll(self, y: int, x: int) -> None:
        self.refresh(self._y + y, self._x + x)

    def refresh(self, y: int, x: int) -> None:
        self._y = clamp(y, 0, self.height - 1)
        self._x = clamp(x, 0, self.width - 1)

        self.pad.refresh(
            self._y, self._x,
            self.offset_y, self.offset_x,
            min(self.height, curses.LINES) - 1, min(self.width, curses.COLS) - 1
        )

def clamp(val: int, minval: int, maxval: int) -> int:
    return max(minval, min(val, maxval))
