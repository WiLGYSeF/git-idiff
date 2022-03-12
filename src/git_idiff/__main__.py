#!/usr/bin/env python3

import sys
import typing

from gitdiff import GitDiff
from ui.cui import CursesUi, curses_initialize

def main(args: typing.List[str]) -> None:
    gitdiff = GitDiff(args)
    cui = CursesUi(gitdiff)
    curses_initialize(cui)

if __name__ == '__main__':
    main(sys.argv[1:])
