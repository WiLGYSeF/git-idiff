import asyncio
import curses
import sys
import typing

from ..gitdiff import GitDiff, GitFile, ProcessError
from .colors import init_colors
from .diff import DiffPad
from .filelist import FileList
from . import loader
from .messagebox import MessageBox
from .statusbar import StatusBar

FILELIST_COLUMN_WIDTH_MIN = 16
FILELIST_COLUMN_WIDTH_MAX_REMAIN = 16
FILELIST_SCROLL_COUNT = 5

WAIT_GET_FILES = 0.15

class CursesUi:
    FILELIST_SCROLL_OFFSET = 1

    CURSES_BUTTON5_PRESSED = 0x00200000 # thanks python

    def __init__(self, gitdiff: GitDiff):
        self.gitdiff = gitdiff

        self.stdscr: curses.window = None

        self.pad_filelist: FileList = None
        self.pad_diff: DiffPad = None
        self.pad_statusbar: StatusBar = None

        self.filelist: typing.List[GitFile] = []
        self.total_insertions: int = 0
        self.total_deletions: int = 0

        self.selected_file: typing.Optional[GitFile] = None
        self.selected_file_idx: int = -1
        self.filelist_border_selected: bool = False

        self.help_menu_visible: bool = False

    async def run(self, stdscr: curses.window) -> None:
        self.stdscr = stdscr
        lines, columns = self.stdscr.getmaxyx()

        curses.curs_set(False)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        init_colors()

        removed_args = self.gitdiff.removed_args
        if len(removed_args) > 0:
            try:
                MessageBox.draw(
                    stdscr,
                    MessageBox.box_msg(
                        [
                            'You supplied unsupported arguments, they will be ignored: ',
                            ', '.join(removed_args),
                            '',
                            'Press any key to continue.'
                        ],
                        min(70, columns - 4)
                    ),
                    title='Unsupported arguments',
                    hspacing=1
                )
                self.stdscr.getch()
            except ValueError:
                pass

        filelist_column_width = columns // 4

        self.pad_filelist = FileList(stdscr, filelist_column_width)
        self.pad_diff = DiffPad(stdscr, self.gitdiff, filelist_column_width)
        self.pad_statusbar = StatusBar(stdscr)

        stdscr.erase()
        stdscr.refresh()

        await self.get_diff_async(update=False)

        if len(self.filelist) == 0:
            return

        await self.get_statuses_async()
        self.select_file(0)

        while True:
            key = self.stdscr.getch()

            if self.help_menu_visible:
                self.update_filelist()
                self.update_diff()
                self.help_menu_visible = False

            if self._handle_key_input(key):
                break
            self.update_statusbar()

    def _handle_key_input(self, key: int) -> bool:
        if key < 256:
            keychr = chr(key)
            if keychr == 'f':
                self.toggle_filelist()
            elif keychr in ('n', 'B'): # ctrl + KEY_DOWN
                self.select_next_file()
            elif keychr in ('p', 'A'): # ctrl + KEY_UP
                self.select_prev_file()
            elif keychr == '?':
                self.show_help_menu()
            elif keychr == 'q':
                return True
        elif key == curses.KEY_UP:
            self.pad_diff.scroll(-1, 0)
        elif key == curses.KEY_DOWN:
            self.pad_diff.scroll(1, 0)
        elif key == curses.KEY_LEFT:
            self.pad_diff.scroll(0, -self.pad_diff.width // 2)
        elif key == curses.KEY_RIGHT:
            self.pad_diff.scroll(0, self.pad_diff.width // 2)
        elif key == curses.KEY_PPAGE:
            self.pad_diff.scroll(-self.pad_diff.height, 0)
        elif key == curses.KEY_NPAGE:
            self.pad_diff.scroll(self.pad_diff.height, 0)
        elif key == curses.KEY_HOME:
            self.pad_diff.refresh(0, 0)
        elif key == curses.KEY_END:
            self.pad_diff.refresh(self.pad_diff.pad.getmaxyx()[0], 0)
        elif key == curses.KEY_MOUSE:
            self._handle_mouse_input()
        elif key == curses.KEY_RESIZE:
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
        return False

    def _handle_mouse_input(self) -> None:
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
                self.select_file(self.pad_filelist.y + mousey)
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
                    self.pad_diff.scroll(0, -FILELIST_SCROLL_COUNT)
                else:
                    self.pad_diff.scroll(-FILELIST_SCROLL_COUNT, 0)
            elif state & CursesUi.CURSES_BUTTON5_PRESSED:
                if state & curses.BUTTON_SHIFT:
                    self.pad_diff.scroll(0, FILELIST_SCROLL_COUNT)
                else:
                    self.pad_diff.scroll(FILELIST_SCROLL_COUNT, 0)

    async def get_diff_async(self, update: bool = True) -> None:
        self.filelist = []
        task = asyncio.create_task(self.gitdiff.get_diff_async())

        self.filelist = await loader.show_loading(
            self.stdscr,
            task,
            'Loading diff',
            WAIT_GET_FILES
        )
        self._get_diff_after(update)

    def get_diff(self, update: bool = True) -> None:
        self.filelist = self.gitdiff.get_diff()
        self._get_diff_after(update)

    def _get_diff_after(self, update: bool = True) -> None:
        if len(self.filelist) != 0:
            self.selected_file = self.filelist[0]

        self.total_insertions = 0
        self.total_deletions = 0

        for file in self.filelist:
            if file.insertions is not None:
                self.total_insertions += file.insertions
            if file.deletions is not None:
                self.total_deletions += file.deletions

        if update:
            self.update_filelist()
            self.update_statusbar()

    async def get_statuses_async(self) -> None:
        task = asyncio.create_task(self.gitdiff.get_statuses_async(self.filelist))
        await loader.show_loading(self.stdscr, task, 'Loading file status', WAIT_GET_FILES)
        self.update_filelist()

    def get_statuses(self) -> None:
        self.gitdiff.get_statuses(self.filelist)

    def select_next_file(self) -> bool:
        if self.selected_file_idx == len(self.filelist) - 1:
            return False

        self.select_file(self.selected_file_idx + 1)
        if self.selected_file_idx - self.pad_filelist.y >= self.pad_filelist.height - CursesUi.FILELIST_SCROLL_OFFSET - 1:
            self.pad_filelist.scroll(1, 0)
        return True

    def select_prev_file(self) -> bool:
        if self.selected_file_idx == 0:
            return False

        self.select_file(self.selected_file_idx - 1)
        if self.selected_file_idx - self.pad_filelist.y <= CursesUi.FILELIST_SCROLL_OFFSET:
            self.pad_filelist.scroll(-1, 0)
        return True

    def select_file(self, idx: int) -> None:
        if idx < 0 or idx >= len(self.filelist):
            return

        self.selected_file_idx = idx
        self.selected_file = self.filelist[self.selected_file_idx]

        self.update_filelist()
        self.update_diff()
        self.update_statusbar()

        self.pad_diff.refresh(0, 0)

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
        if self.selected_file is not None:
            headers = self.selected_file.headers
            content = self.selected_file.content
        else:
            headers = []
            content = []

        self.pad_diff.update(
            headers,
            content,
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

    def show_help_menu(self) -> None:
        try:
            MessageBox.draw(self.stdscr, [
                '  use arrow keys to navigate diff  ',
                '  n  select next file',
                '  p  select previous file',
                '  f  toggle file list',
                '',
                '  q  quit'
            ], title='Help menu')
            self.stdscr.refresh()
            self.help_menu_visible = True
        except ValueError:
            pass

    def diff_lines(self) -> int:
        if self.selected_file is None:
            return 0
        return len(self.selected_file.headers) + len(self.selected_file.content)

    def diff_longest_line(self) -> int:
        if self.selected_file is None:
            return 0
        return max(
            max( len(line) for line in self.selected_file.headers ) if len(self.selected_file.headers) != 0 else 0,
            max( len(line) for line in self.selected_file.content )  if len(self.selected_file.content) != 0 else 0
        ) if self.diff_lines() != 0 else 0

def curses_initialize(cui: CursesUi) -> None:
    try:
        curses.wrapper(lambda stdscr: _main(cui, stdscr))
    except ProcessError as err:
        print(err, end='', file=sys.stderr)

def _main(cui: CursesUi, stdscr: curses.window) -> None:
    asyncio.run(cui.run(stdscr))
