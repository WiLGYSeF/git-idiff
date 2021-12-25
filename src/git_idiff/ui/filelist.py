import curses

import ui.colors
from ui.pad import CursesPad

class FileList(CursesPad):
    def __init__(self, stdscr, column_width: int):
        self.column_width: int = column_width

        lines, _ = stdscr.getmaxyx()

        super().__init__(stdscr,
            height = lines - 1,
            width = self.column_width,
            offset_y = 0,
            offset_x = 0
        )

        self.visible: bool = True

    def update(self, filelist, selected_file_idx) -> None:
        if not self.visible:
            return

        self.pad.erase()

        max_y, max_x = self.pad.getmaxyx()
        if len(filelist) >= max_y:
            self.pad.resize(len(filelist) + 1, max_x)

        # create a right border and decrease max_x to account for it
        self.pad.border(
            ' ', 0, ' ', ' ',
            ' ', curses.ACS_VLINE, ' ', curses.ACS_VLINE
        )
        max_x -= 1

        idx = 0
        for file in filelist:
            fname = file.filename
            added = file.insertions
            removed = file.deletions

            if added is not None:
                added_str = str(added)
            else:
                added_str = '-'

            if removed is not None:
                removed_str = str(removed)
            else:
                removed_str = '-'

            total_length = len(f'{added_str} {removed_str} {fname}')
            length = 0

            if total_length > max_x:
                fname = '##' + fname[
                    max(len(fname) - (max_x - len(f'{added_str} {removed_str} ##')), 0)
                    :
                ]

            def write(val, attr=curses.A_NORMAL):
                nonlocal length

                if idx == selected_file_idx:
                    attr |= curses.A_REVERSE

                if length + len(val) >= max_x:
                    val = val[len(val) - (max_x - length):]
                if len(val) > 0:
                    self.pad.addstr(idx, length, val, attr)
                    length += len(val)

            write(added_str, curses.color_pair(ui.colors.COLOR_ADD))
            write(' ')
            write(removed_str, curses.color_pair(ui.colors.COLOR_REMOVE))
            write(' ')
            write(' ' * (max_x - length - len(fname)))
            write(fname)
            idx += 1

        self.refresh(self.y, 0)
