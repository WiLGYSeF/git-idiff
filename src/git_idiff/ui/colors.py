import curses

COLOR_ADD = 1
COLOR_REMOVE = 2
COLOR_SECTION = 3
COLOR_HEADER = 4
COLOR_CHANGE = 5

def init_colors() -> None:
    curses.use_default_colors()
    curses.init_pair(COLOR_ADD, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_REMOVE, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_SECTION, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_HEADER, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOR_CHANGE, curses.COLOR_YELLOW, -1)
