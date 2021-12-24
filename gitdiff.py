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

def get_file_diff(fname: str) -> typing.List[str]:
    output = subprocess.check_output([
        'git', 'diff', fname
    ])
    lines = output.decode('utf-8').split('\n')
    headers = []
    idx = 0

    header_starts =  ['diff ', 'index ', '--- ', '+++ ']

    while idx < len(header_starts):
        if not lines[idx].startswith(header_starts[idx]):
            break
        idx += 1

    for _ in range(idx):
        headers.append(lines.pop(0))

    return lines

def _sanitize_args(args: typing.List[str]) -> typing.List[str]:
    return list(filter(lambda a: a[0] != '-', args))
