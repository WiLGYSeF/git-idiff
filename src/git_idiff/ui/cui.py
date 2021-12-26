import asyncio
import curses
import typing

from gitdiff import GitDiff, GitFile
from ui.colors import init_colors
from ui.diff import DiffPad
from ui.filelist import FileList
from ui.messagebox import MessageBox
from ui.statusbar import StatusBar

FILELIST_COLUMN_WIDTH = 24
FILELIST_COLUMN_WIDTH_MIN = 16
FILELIST_COLUMN_WIDTH_MAX_REMAIN = 16

WAIT_GET_FILES = 0.15

class CursesUi:
    FILELIST_SCROLL_OFFSET = 1

    CURSES_BUTTON5_PRESSED = 0x00200000 # thanks python

    def __init__(self, diff_args: typing.Optional[typing.List[str]] = None):
        self.gitdiff: GitDiff = GitDiff(diff_args)

        self.stdscr: curses.window = None

        self.pad_filelist: FileList = None
        self.pad_diff: DiffPad = None
        self.pad_statusbar: StatusBar = None

        self.filelist: typing.List[GitFile] = []
        self.total_insertions: int = 0
        self.total_deletions: int = 0

        self.diff_headers: typing.List[str] = []
        self.diff_contents: typing.List[str] = []

        self.selected_file: typing.Optional[str] = None
        self.selected_file_idx: int = -1
        self.filelist_border_selected: bool = False

    async def run(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr

        curses.curs_set(False)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        init_colors()

        self.pad_filelist = FileList(stdscr, FILELIST_COLUMN_WIDTH)
        self.pad_diff = DiffPad(stdscr, self.gitdiff, FILELIST_COLUMN_WIDTH)
        self.pad_statusbar = StatusBar(stdscr)

        stdscr.erase()
        stdscr.refresh()

        await self.get_files_async()

        if len(self.filelist) == 0:
            return

        self._select_file(0)

        while True:
            c = self.stdscr.getch()
            if c < 256:
                ch = chr(c)
                if ch == 'f':
                    self.toggle_filelist()
                elif ch == 'n':
                    self.select_next_file()
                elif ch == 'p':
                    self.select_prev_file()
                elif ch == 'q':
                    break
            elif c == curses.KEY_UP:
                self.pad_diff.scroll(-1, 0)
            elif c == curses.KEY_DOWN:
                self.pad_diff.scroll(1, 0)
            elif c == curses.KEY_LEFT:
                self.pad_diff.scroll(0, -1)
            elif c == curses.KEY_RIGHT:
                self.pad_diff.scroll(0, 1)
            elif c == curses.KEY_PPAGE:
                self.pad_diff.scroll(-self.pad_diff.height, 0)
            elif c == curses.KEY_NPAGE:
                self.pad_diff.scroll(self.pad_diff.height, 0)
            elif c == curses.KEY_HOME:
                self.pad_diff.refresh(self.pad_diff.y, 0)
            elif c == curses.KEY_END:
                self.pad_diff.refresh(self.pad_diff.y, self.pad_diff.pad.getmaxyx()[1])
            elif c == curses.KEY_MOUSE:
                self._handle_mouse_input()
            elif c == curses.KEY_RESIZE:
                lines, columns = self.stdscr.getmaxyx()
                self.pad_filelist.height = lines - 1
                self.pad_diff.height = lines - 1
                self.pad_statusbar.offset_y = lines - 1
                self.pad_diff.width = columns - self.pad_filelist.column_width
                self.pad_statusbar.width = columns

                self.stdscr.erase()
                self.stdscr.refresh()

                self.update_filelist()
                self.update_diff()

            self.update_statusbar()

    def _handle_mouse_input(self):
        try:
            result = curses.getmouse()
        except curses.error:
            return

        _, mousex, mousey, _, state = result

        if state & curses.BUTTON1_RELEASED:
            if self.filelist_border_selected:
                self.set_filelist_column_width(mousex + 1)
            self.filelist_border_selected = False

        if self.pad_filelist.pad.enclose(mousey, mousex) and self.pad_filelist.visible:
            if state & curses.BUTTON1_CLICKED:
                self._select_file(self.pad_filelist.y + mousey)
            elif state & curses.BUTTON1_PRESSED:
                if mousex == self.pad_filelist.column_width - 1:
                    self.filelist_border_selected = True
            elif state & curses.BUTTON4_PRESSED:
                self.select_prev_file()
            elif state & CursesUi.CURSES_BUTTON5_PRESSED:
                self.select_next_file()
        elif self.pad_diff.pad.enclose(mousey, mousex):
            if state & curses.BUTTON4_PRESSED:
                if state & curses.BUTTON_SHIFT:
                    self.pad_diff.scroll(0, -5)
                else:
                    self.pad_diff.scroll(-5, 0)
            elif state & CursesUi.CURSES_BUTTON5_PRESSED:
                if state & curses.BUTTON_SHIFT:
                    self.pad_diff.scroll(0, 5)
                else:
                    self.pad_diff.scroll(5, 0)

    async def get_files_async(self) -> None:
        self.filelist = []
        loadchars = r'/-\|'
        counter = 0

        task = asyncio.create_task(self.gitdiff.get_filenames_async())

        while True:
            try:
                filelist = await asyncio.wait_for(asyncio.shield(task), timeout=WAIT_GET_FILES)
                break
            except asyncio.TimeoutError:
                pass

            self.stdscr.erase()

            MessageBox.draw(self.stdscr, [
                '',
                f'   Loading... {loadchars[counter]}   ',
                ''
            ])

            counter += 1
            if counter == len(loadchars):
                counter = 0

            self.stdscr.refresh()

        self.stdscr.erase()
        self.stdscr.refresh()

        self.filelist = filelist
        self._get_files()

    def get_files(self) -> None:
        self.filelist = self.gitdiff.get_filenames()
        self._get_files()

    def _get_files(self) -> None:
        self.total_insertions = 0
        self.total_deletions = 0

        for file in self.filelist:
            if file.insertions is not None:
                self.total_insertions += file.insertions
            if file.deletions is not None:
                self.total_deletions += file.deletions

        self.update_filelist()
        self.update_statusbar()

    def select_next_file(self) -> bool:
        if self.selected_file_idx == len(self.filelist) - 1:
            return False

        self._select_file(self.selected_file_idx + 1)
        if self.selected_file_idx - self.pad_filelist.y >= self.pad_filelist.height - CursesUi.FILELIST_SCROLL_OFFSET - 1:
            self.pad_filelist.scroll(1, 0)
        return True

    def select_prev_file(self) -> bool:
        if self.selected_file_idx == 0:
            return False

        self._select_file(self.selected_file_idx - 1)
        if self.selected_file_idx - self.pad_filelist.y <= CursesUi.FILELIST_SCROLL_OFFSET:
            self.pad_filelist.scroll(-1, 0)
        return True

    def _select_file(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.filelist):
            return

        if idx != self.selected_file_idx:
            self.selected_file_idx = idx
            self.selected_file = self.filelist[self.selected_file_idx][0]
            self.get_file_diff()

        self.update_filelist()
        self.update_diff()
        self.update_statusbar()

        self.pad_diff.refresh(0, 0)

    def get_file_diff(self) -> None:
        self.diff_headers, self.diff_contents = self.gitdiff.get_file_diff(self.selected_file)

    def toggle_filelist(self) -> None:
        if self.pad_filelist.visible:
            self.pad_filelist.visible = False
            self.pad_diff.offset_x -= self.pad_filelist.column_width
            self.pad_diff.width += self.pad_filelist.column_width

            self.stdscr.erase()
            self.stdscr.refresh()

            self.pad_filelist.pad.erase()
            self.pad_filelist.refresh(0, 0)
        else:
            self.pad_filelist.visible = True
            self.pad_diff.offset_x += self.pad_filelist.column_width
            self.pad_diff.width -= self.pad_filelist.column_width

            self.pad_filelist.scroll(
                self.selected_file_idx - self.pad_filelist.y - CursesUi.FILELIST_SCROLL_OFFSET - 1,
                0
            )
            self.update_filelist()

        self.update_diff()

    def set_filelist_column_width(self, width: int) -> None:
        if width == self.pad_filelist.column_width:
            return

        _, columns = self.stdscr.getmaxyx()
        self.pad_filelist.column_width = max(
            min(width, columns - FILELIST_COLUMN_WIDTH_MAX_REMAIN),
            FILELIST_COLUMN_WIDTH_MIN
        )

        self.pad_diff.width = columns - self.pad_filelist.column_width
        self.pad_diff.offset_x = self.pad_filelist.column_width
        self.stdscr.erase()
        self.stdscr.refresh()
        self.update_filelist()
        self.update_diff()

    def update_filelist(self) -> None:
        self.pad_filelist.update(self.filelist, self.selected_file_idx)

    def update_diff(self) -> None:
        self.pad_diff.update(
            self.diff_headers,
            self.diff_contents,
            self.diff_lines(),
            self.diff_longest_line()
        )

    def update_statusbar(self) -> None:
        self.pad_statusbar.update(
            self.pad_diff,
            self.diff_lines(),
            self.diff_longest_line(),
            self.selected_file_idx,
            len(self.filelist),
            self.total_insertions,
            self.total_deletions
        )

    def diff_lines(self) -> int:
        return len(self.diff_headers) + len(self.diff_contents)

    def diff_longest_line(self) -> int:
        return max(
            max( len(line) for line in self.diff_headers ),
            max( len(line) for line in self.diff_contents )
        ) if self.diff_lines() != 0 else 0

def curses_initialize(cui: CursesUi) -> None:
    curses.wrapper(lambda stdscr: _main(cui, stdscr))

def _main(cui: CursesUi, stdscr: curses.window) -> None:
    asyncio.run(cui.run(stdscr))
