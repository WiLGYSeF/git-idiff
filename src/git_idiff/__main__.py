#!/usr/bin/env python3

import sys
import typing

from . import __version__
from .gitdiff import GitDiff
from .ui.cui import CursesUi, curses_initialize

def main(args: typing.List[str]) -> None:
    if len(args) > 0 and args[0] == '-V':
        print(__version__)
        sys.exit(0)

    gitdiff = GitDiff(args)
    cui = CursesUi(gitdiff)
    curses_initialize(cui)

def main_args():
    main(sys.argv[1:])

if __name__ == '__main__':
    main_args()
