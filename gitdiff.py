import re
import subprocess
import typing

class GitFile(typing.NamedTuple):
    filename: str
    old_filename: typing.Optional[str]
    insertions: typing.Optional[int]
    deletions: typing.Optional[int]

FileList = typing.List[GitFile]

def get_filenames(
    args: typing.Optional[typing.List[str]] = None
) -> FileList:
    cmdargs = ['git', 'diff', '--numstat', '-z']
    if args is not None:
        cmdargs.extend(_sanitize_args(args))

    output = subprocess.check_output(cmdargs)
    output_split = output.split(b'\0')
    idx = 0

    results: FileList = []

    while idx < len(output_split):
        parts = output_split[idx].split(b'\t')
        idx += 1
        if len(parts) != 3:
            continue

        insertions, deletions, fname = parts
        oldfname = None

        if len(fname) == 0:
            oldfname = output_split[idx].decode('utf-8')
            idx += 1
            fname = output_split[idx]
            idx += 1

        results.append(GitFile(
            fname.decode('utf-8'),
            oldfname,
            int(parts[0]) if parts[0] != b'-' else None,
            int(parts[1]) if parts[1] != b'-' else None
        ))

    return results

def get_file_diff(
    fname: str,
    args: typing.Optional[typing.List[str]] = None
) -> typing.Tuple[typing.List[str], typing.List[str]]:
    cmdargs = ['git', 'diff']
    if args is not None:
        cmdargs.extend(_sanitize_args(args))
    cmdargs.extend(('--', fname))

    output = subprocess.check_output(cmdargs)
    lines = output.decode('utf-8').split('\n')

    headers_regex = re.compile(
        r'^(diff|(old|new) mode|(new|deleted) file|copy|rename|((dis)?similarity )?index|---|\+\+\+) '
    )
    headers = []

    while len(lines) > 0:
        if headers_regex.search(lines[0]) is None:
            break
        headers.append(lines.pop(0))

    return headers, lines

def _sanitize_args(args: typing.List[str]) -> typing.List[str]:
    result = []

    for arg in args:
        if arg == '--':
            break
        if arg[0] == '-':
            continue
        result.append(arg)

    return result
