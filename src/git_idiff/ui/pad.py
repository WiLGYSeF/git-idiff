from abc import ABC, abstractmethod
import curses

class CursesPad(ABC):
    def __init__(self, window, **kwargs):
        self.window = window
        self.height: int = kwargs['height']
        self.width: int = kwargs['width']
        self.offset_y: int = kwargs['offset_y']
        self.offset_x: int = kwargs['offset_x']

        self.pad = curses.newpad(self.height, self.width)

        self._y: int = 0
        self._x: int = 0

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def scroll(self, offy: int, offx: int) -> None:
        self.refresh(self._y + offy, self._x + offx)

    def refresh(self, y: int, x: int) -> None:
        wmax_y, wmax_x = self.window.getmaxyx()
        pmax_y, pmax_x = self.pad.getmaxyx()

        self._y = _clamp(y, 0, pmax_y - self.height - 1)
        self._x = _clamp(x, 0, pmax_x - self.width - 1)

        self.pad.refresh(
            self._y, self._x,
            self.offset_y, self.offset_x,
            min(self.height + self.offset_y, wmax_y) - 1,
            min(self.width + self.offset_x, wmax_x) - 1
        )

def _clamp(val: int, minval: int, maxval: int) -> int:
    return max(minval, min(val, maxval))
