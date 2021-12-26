import asyncio
import re
import subprocess
import typing

class GitFile:
    ADDED = 'A'
    COPIED = 'C'
    DELETED = 'D'
    MODIFIED = 'M'
    RENAMED = 'R'
    TYPE_CHANGED = 'T'
    UNMERGED = 'U'
    UNKNOWN = 'X'
    BROKEN = 'B'

    def __init__(self,
        filename: str,
        old_filename: typing.Optional[str] = None,
        insertions: typing.Optional[int] = None,
        deletions: typing.Optional[int] = None,
        headers: typing.Optional[typing.List[str]] = None,
        content: typing.Optional[typing.List[str]] = None,
        status: typing.Optional[str] = None
    ):
        self.filename: str = filename
        self.old_filename: typing.Optional[str] = old_filename
        self.insertions: typing.Optional[int] = insertions
        self.deletions: typing.Optional[int] = deletions
        self.headers: typing.List[str] = headers if headers is not None else []
        self.content: typing.List[str] = content if content is not None else []

        self.status: str = GitFile.UNKNOWN
        self.score: int = 0

        self.set_status(status)

    def set_status(self, status) -> None:
        if status is not None:
            self.status = status[0]
            self.score = int(status[1:]) if len(status) > 1 else 0
        else:
            self.status = GitFile.UNKNOWN
            self.score = 0

_FileDiff = typing.Tuple[typing.List[str], typing.List[str]]

class GitDiff:
    WHITELIST_ARGS = [
        '--no-index',
        '--cached', '--staged',
        '--merge-base',
        '--unified',
        '--indent-heuristic', '--no-indent-heuristic',
        '--minimal',
        '--patience', '--histogram', '--anchored', '--diff-algorithm',
        '--full-index',
        '--break-rewrites',
        '--find-renames',
        '--find-copies', '--find-copies-harder',
        '--irreversible-delete',
        '--diff-filter',
        '--find-object',
        '--pickaxe-all',
        '--pickaxe-regex',
        '--skip-to', '--rotate-to',
        '--relative', '--no-relative',
        '--text',
        '--ignore-cr-at-eol', '--ignore-space-at-eol',
        '--ignore-space-change', '--ignore-all-space', '--ignore-blank-lines',
        '--ignore-matching-lines',
        '--inter-hunk-context', '--function-context',
        '--ext-diff', '--no-ext-diff',
        '--textconv', '--no-textconv',
        '--ignore-submodules',
        '--src-prefix', '--dst-prefix', '--no-prefix',
        '--line-prefix',
        '--ita-invisible-in-index', '--ita-visible-in-index',
        '--base', '--ours', '--theirs',
    ]
    WHITELIST_ARGS_SINGLE = 'DRabwW1230'
    WHITELIST_ARGS_SINGLE_PARAM = 'UBMClSGOI'

    HEADERS_REGEX = re.compile(
        r'^(diff|(old|new) mode|(new|deleted) file|copy|rename|((dis)?similarity )?index|---|\+\+\+) '
    )
    DIFFSTART_REGEX = re.compile(
        r'^diff --git '
    )

    def __init__(self, args: typing.Optional[typing.Iterable[str]] = None):
        self.src_prefix: str = 'a/'
        self.dst_prefix: str = 'b/'
        self.line_prefix: str = ''

        self.args = self._sanitize_args(args) if args is not None else []

    async def get_diff_async(self) -> typing.List[GitFile]:
        proc = await asyncio.create_subprocess_exec(*[
            'git', 'diff', '--numstat', '-z', '-p', *self.args
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = await proc.communicate()

        return self._get_diff(output)

    def get_diff(self) -> typing.List[GitFile]:
        return self._get_diff(subprocess.check_output([
            'git', 'diff', '--numstat', '-z', '-p', *self.args
        ]))

    def _get_diff(self, output: bytes) -> typing.List[GitFile]:
        output_split = output.split(b'\0')
        idx = 0

        results: typing.List[GitFile] = []

        while idx < len(output_split):
            parts = self.noprefix(output_split[idx]).split(b'\t')
            idx += 1
            if len(parts) == 1:
                break

            insertions, deletions, fname = parts
            old_fname = None

            try:
                if len(fname) == 0:
                    old_fname = self.noprefix(output_split[idx]).decode('utf-8')
                    idx += 1
                    fname = self.noprefix(output_split[idx])
                    idx += 1

                    if len(fname) == 0 or len(old_fname) == 0:
                        raise ValueError('missing filename')

                results.append(GitFile(
                    fname.decode('utf-8'),
                    old_fname,
                    int(insertions) if insertions != b'-' else None,
                    int(deletions) if deletions != b'-' else None
                ))
            except (IndexError, ValueError) as err:
                raise ValueError('received incorrect output from git diff') from err

        # git diff did not return a patch
        if idx == len(output_split):
            return results

        result_idx = 0
        for filediff in self._get_file_diffs(output_split[idx].decode('utf-8')):
            headers, content = filediff

            if result_idx == len(results):
                raise ValueError(
                    f'too many diff patches were given for all of the changes, only expected {len(results)}'
                )

            results[result_idx].headers = headers
            results[result_idx].content = content
            result_idx += 1

        if result_idx != len(results):
            raise ValueError(
                f'not enough diff patches were given for all of the changes, expected {len(results)}, but got {result_idx}'
            )

        return results

    def _get_file_diffs(self, data: str) -> typing.Generator[_FileDiff, None, None]:
        lines = data.split('\n')
        start = 0
        idx = 0

        while idx < len(lines):
            if GitDiff.DIFFSTART_REGEX.search(lines[idx]) is not None:
                if start != idx:
                    yield self._get_file_diff(lines, start, idx)
                    start = idx
            idx += 1

        if start != idx:
            yield self._get_file_diff(lines, start, idx)

    def _get_file_diff(self, lines: typing.List[str], start: int, end: int) -> _FileDiff:
        idx = start
        while idx < end:
            if GitDiff.HEADERS_REGEX.search(self.noprefix(lines[idx])) is None:
                break
            idx += 1

        return lines[start:idx], lines[idx:end]

    async def get_statuses_async(self, files: typing.List[GitFile]) -> None:
        proc = await asyncio.create_subprocess_exec(*[
            'git', 'diff', '--name-status', '-z', *self.args
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = await proc.communicate()

        self._get_statuses(files, output)

    def get_statuses(self, files: typing.List[GitFile]) -> None:
        self._get_statuses(files, subprocess.check_output([
            'git', 'diff', '--name-status', '-z', *self.args
        ]))

    def _get_statuses(self, files: typing.List[GitFile], output: bytes) -> None:
        output_split = output.split(b'\0')
        idx = 0

        filemap: typing.Dict[str, GitFile] = {}
        for file in files:
            filemap[file.filename] = file

        while idx < len(output_split) and len(output_split[idx]) > 0:
            try:
                status = output_split[idx].decode('utf-8')
                idx += 1
                fname = output_split[idx].decode('utf-8')
                idx += 1

                old_fname = None

                if fname not in filemap:
                    old_fname = fname
                    fname = output_split[idx].decode('utf-8')
                    idx += 1

                    if fname not in filemap:
                        raise ValueError(f'filename is not in results: {fname}')

                file = filemap[fname]
                file.set_status(status)

                if old_fname != file.old_filename:
                    raise ValueError(
                        f'expected a src filename of {file.old_filename}, but got {old_fname}'
                    )
            except (IndexError, ValueError) as err:
                raise ValueError('received incorrect output from git diff') from err

    def _sanitize_args(self, args: typing.Iterable[str]) -> typing.List[str]:
        result = []

        for arg in args:
            if arg == '--':
                break
            if arg[0] == '-':
                if len(arg) > 1:
                    if arg[1] != '-':
                        idx = 1
                        while idx < len(arg) and not arg[idx] in GitDiff.WHITELIST_ARGS_SINGLE_PARAM:
                            if arg[idx] not in GitDiff.WHITELIST_ARGS_SINGLE:
                                arg = arg[:idx] + arg[idx + 1:]
                            else:
                                idx += 1
                        if len(arg) == 1:
                            continue
                    else:
                        if not any(arg.startswith(warg) for warg in GitDiff.WHITELIST_ARGS):
                            continue
                        if arg.startswith('--src-prefix='):
                            self.src_prefix = arg[len('--src-prefix='):]
                        if arg.startswith('--dst-prefix='):
                            self.dst_prefix = arg[len('--dst-prefix='):]
                        if arg.startswith('--line-prefix='):
                            self.line_prefix = arg[len('--line-prefix='):]
            result.append(arg)

        return result

    def has_prefix(self) -> bool:
        return len(self.line_prefix) != 0

    def noprefix(self, val: typing.AnyStr) -> typing.AnyStr:
        return val[len(self.line_prefix):] if len(self.line_prefix) != 0 else val
