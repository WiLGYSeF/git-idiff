import asyncio
import curses
import typing

from .messagebox import MessageBox

async def show_loading(
    win: curses.window,
    task: asyncio.Task,
    message: str,
    wait_interval: float
) -> typing.Any:
    loadchars = r'/-\|'
    counter = 0

    win.erase()
    win.refresh()

    while True:
        try:
            result = await asyncio.wait_for(asyncio.shield(task), timeout=wait_interval)
            break
        except asyncio.TimeoutError:
            pass

        win.erase()
        MessageBox.draw(win, [
            '',
            f'   {message}... {loadchars[counter]}   ',
            ''
        ])
        counter += 1
        if counter == len(loadchars):
            counter = 0
        win.refresh()

    return result
