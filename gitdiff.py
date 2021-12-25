import re
import subprocess
import typing

FileList = typing.List[
    typing.Tuple[str, typing.Optional[int], typing.Optional[int]]
]

def get_filenames(
    args: typing.Optional[typing.List[str]] = None
) -> FileList:
    cmdargs = ['git', 'diff', '--numstat']
    if args is not None:
        cmdargs.extend(_sanitize_args(args))

    output = subprocess.check_output(cmdargs)
    return [
        (
            part[2],
            int(part[0]) if part[0] != '-' else None,
            int(part[1]) if part[1] != '-' else None
        ) for part in filter(
            lambda x: len(x) == 3,
            ( line.decode('utf-8').split('\t') for line in output.split(b'\n') )
        )
    ]

def get_file_diff(
    fname: str,
    args: typing.Optional[typing.List[str]] = None
) -> typing.List[str]:
    cmdargs = ['git', 'diff']
    if args is not None:
        cmdargs.extend(_sanitize_args(args))
    cmdargs.extend(('--', fname))

    output = subprocess.check_output(cmdargs)
    lines = output.decode('utf-8').split('\n')

    """
    headers = []
    idx = 0

    headers_regex = re.compile(r'^(diff|index|(new|deleted) file|---|\+\+\+) ')

    while idx < len(lines):
        if headers_regex.search(lines[idx]) is None:
            break
        idx += 1

    for _ in range(idx):
        headers.append(lines.pop(0))
    """

    return lines

def _sanitize_args(args: typing.List[str]) -> typing.List[str]:
    result = []

    for arg in args:
        if arg == '--':
            break
        if arg[0] == '-':
            continue
        result.append(arg)

    return result
