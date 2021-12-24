import curses

class UiCurses:
    def __init__(self):
        self.stdscr = None

    def start(self, stdscr):
        self.stdscr = stdscr

        self.stdscr.erase()
        self.stdscr.addstr(0, 0, 'aaaaaa')
        self.stdscr.refresh()
        self.stdscr.getkey()

def initialize(ui: UiCurses) -> None:
    curses.wrapper(ui.start)
