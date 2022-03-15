import curses
import typing

from .vector import Vector

class MessageBox:
    @staticmethod
    def draw(win: curses.window, message: typing.List[str], **kwargs) -> None:
        title: str = kwargs.get('title', '')
        offset_y: int = kwargs.get('offset_y', -1)
        offset_x: int = kwargs.get('offset_x', -1)
        hspacing: int = max(kwargs.get('hspacing', 0), 0)
        vspacing: int = max(kwargs.get('vspacing', 0), 0)
        ls: int = kwargs.get('ls', curses.ACS_VLINE)
        rs: int = kwargs.get('rs', curses.ACS_VLINE)
        ts: int = kwargs.get('ts', curses.ACS_HLINE)
        bs: int = kwargs.get('bs', curses.ACS_HLINE)
        tl: int = kwargs.get('tl', curses.ACS_ULCORNER)
        tr: int = kwargs.get('tl', curses.ACS_URCORNER)
        bl: int = kwargs.get('tl', curses.ACS_LLCORNER)
        br: int = kwargs.get('tl', curses.ACS_LRCORNER)

        lines, columns = win.getmaxyx()
        data_lines = len(message)
        data_columns = max( len(line) for line in message )
        box_lines = data_lines + vspacing * 2 + 2
        box_columns = data_columns + hspacing * 2 + 2

        if box_lines > lines or box_columns > columns:
            raise ValueError(
                f'message exceeds available window space {box_lines}, {box_columns} > {lines}, {columns}'
            )

        topleft = Vector(
            (lines - box_lines) // 2 if offset_y < 0 else offset_y,
            (columns - box_columns) // 2 if offset_x < 0 else offset_x
        )
        topright = topleft + Vector(0, box_columns - 1)
        botleft = topleft + Vector(box_lines - 1, 0)
        botright = botleft + Vector(0, box_columns - 1)
        width = topright.x - topleft.x - 1

        # draw corners
        _addch(win, topleft, tl)
        _addch(win, topright, tr)
        _addch(win, botleft, bl)
        _addch(win, botright, br)

        # draw top line and title
        cur = topleft.copy()
        _addch(win, cur.add(0, 1), ts)
        cur.add(0, _addnstr(win, cur.add(0, 1), title, box_columns - 3) - 1)
        while cur.x < topright.x - 1:
            _addch(win, cur.add(0, 1), ts)

        # draw right line
        cur = topright.copy()
        while cur.y < botright.y - 1:
            _addch(win, cur.add(1, 0), rs)

        # draw left line
        cur = topleft.copy()
        while cur.y < botright.y - 1:
            _addch(win, cur.add(1, 0), ls)

        # draw bottom line
        cur = botleft.copy()
        while cur.x < botright.x - 1:
            _addch(win, cur.add(0, 1), bs)

        cur = topleft + Vector(vspacing, 1 + hspacing)
        for line in message:
            _addnstr(win, cur.add(1, 0), line + ' ' * (width - len(line)), width)

    @staticmethod
    def box_msg(message: typing.List[str], width: int) -> typing.List[str]:
        result = []

        for line in message:
            while len(line) > width:
                result.append(line[:width])
                line = line[width:]
            result.append(line)

        return result

def _addch(win: curses.window, vec: Vector, val: int) -> None:
    win.addch(vec.y, vec.x, val)

def _addnstr(win: curses.window, vec: Vector, val: str, n: int) -> int:
    win.addnstr(vec.y, vec.x, val, n)
    return min(len(val), n)
