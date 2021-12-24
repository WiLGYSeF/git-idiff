import subprocess
import typing

def get_filenames(
    args: typing.Optional[typing.List[str]] = None
) -> typing.List[typing.Tuple[str, int, int]]:
    cmdargs = ['git', 'diff', '--numstat']
    if args is not None:
        cmdargs.extend(_sanitize_args(args))

    output = subprocess.check_output(cmdargs)
    return [
        (part[2], int(part[0]), int(part[1])) for part in filter(
            lambda x: len(x) == 3,
            ( line.decode('utf-8').split('\t') for line in output.split(b'\n') )
        )
    ]

def _sanitize_args(args: typing.List[str]) -> typing.List[str]:
    return list(filter(lambda a: a[0] != '-', args))
