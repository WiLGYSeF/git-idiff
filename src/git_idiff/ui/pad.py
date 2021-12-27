from abc import ABC
import curses

class CursesPad(ABC):
    def __init__(self, win: curses.window, **kwargs):
        self.window: curses.window = win
        self._height: int = kwargs['height']
        self._width: int = kwargs['width']
        self._offset_y: int = kwargs['offset_y']
        self._offset_x: int = kwargs['offset_x']

        self.pad: curses.window = curses.newpad(self.height, self.width)

        self._visible: bool = True
        self._y: int = 0
        self._x: int = 0

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, val: int) -> None:
        if val < 1:
            raise ValueError()

        if val != self._height:
            self._height = val
            self.refresh(self._y, self._x)

    @property
    def width(self) -> int:
        return self._width

    @width.setter
    def width(self, val: int) -> None:
        if val < 1:
            raise ValueError()

        if val != self._width:
            self._width = val
            self.refresh(self._y, self._x)

    @property
    def offset_y(self) -> int:
        return self._offset_y

    @offset_y.setter
    def offset_y(self, val: int) -> None:
        if val < 0:
            raise ValueError()

        if val != self._offset_y:
            self._offset_y = val
            self.refresh(self._y, self._x)

    @property
    def offset_x(self) -> int:
        return self._offset_x

    @offset_x.setter
    def offset_x(self, val: int) -> None:
        if val < 0:
            raise ValueError()

        if val != self._offset_x:
            self._offset_x = val
            self.refresh(self._y, self._x)

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, val: bool) -> None:
        self._visible = val

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def scroll(self, offy: int, offx: int) -> None:
        self.refresh(self._y + offy, self._x + offx)

    def refresh(self, y: int, x: int) -> None:
        wmax_y, wmax_x = self.window.getmaxyx()
        pmax_y, pmax_x = self.pad.getmaxyx()

        self._y = _clamp(y, 0, pmax_y - self._height - 1)
        self._x = _clamp(x, 0, pmax_x - self._width - 1)

        if self._visible:
            self.pad.refresh(
                self._y, self._x,
                min(self._offset_y, wmax_y - 1), min(self._offset_x, wmax_x - 1),
                min(self._height + self._offset_y, wmax_y) - 1,
                min(self._width + self._offset_x, wmax_x) - 1
            )

    def resize(self, max_y: int, max_x: int) -> None:
        if max_y < 1 or max_x < 1:
            raise ValueError()

        self._height = max_y
        self._width = max_x

        self._y = min(self._y, max_y)
        self._x = min(self._x, max_x)

        self.pad.resize(max_y, max_x)

def _clamp(val: int, minval: int, maxval: int) -> int:
    return max(minval, min(val, maxval))
