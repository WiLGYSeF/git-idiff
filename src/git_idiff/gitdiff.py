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
        '--ita-invisible-in-index', '--ita-visible-in-index',
        '--base', '--ours', '--theirs',
    ]
    WHITELIST_ARGS_SINGLE = 'DRabwW1230'
    WHITELIST_ARGS_SINGLE_PARAM = 'UBMClSGOI'
    BLACKLIST_ARGS_SINGLE_PARAM = 'X'

    HEADERS_REGEX = re.compile(
        r'^(%s) ' % ('|'.join([
            'diff',
            '(old|new) mode',
            'index',
            'mode',
            '(new|deleted) file mode',
            'copy (from|to)',
            'rename (from|to)',
            '(dis)?similarity index',
            'index',
            '---',
            r'\+\+\+',
        ]))
    )
    DIFFSTART_REGEX = re.compile(
        r'^diff --(cc|git) '
    )

    DIFF_ARGS = ['git', 'diff', '--numstat', '-z', '-p']
    STATUS_ARGS = ['git', 'diff', '--name-status', '-z']

    def __init__(self, args: typing.Optional[typing.Iterable[str]] = None):
        self.src_prefix: str = 'a/'
        self.dst_prefix: str = 'b/'
        self._removed_args: typing.List[str] = []

        self.args = self._sanitize_args(args) if args is not None else []

    async def get_diff_async(self) -> typing.List[GitFile]:
        """
        Gets git diff patch output and processes it
        """
        proc = await asyncio.create_subprocess_exec(*[
            *GitDiff.DIFF_ARGS, *self.args
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise ProcessError(stderr.decode('utf-8'))

        return self._process_diff(output)

    def get_diff(self) -> typing.List[GitFile]:
        """
        Gets git diff patch output and processes it
        """
        with subprocess.Popen([
            *GitDiff.DIFF_ARGS, *self.args
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            output, stderr = proc.communicate()
            if proc.returncode != 0:
                raise ProcessError(stderr.decode('utf-8'))

            return self._process_diff(output)

    def _process_diff(self, output: bytes) -> typing.List[GitFile]:
        """
        Processes git diff patch output into GitFile entries
        """
        output_split = output.split(b'\0')
        idx = 0

        results: typing.List[GitFile] = []

        # check for merge conflict patches
        merge_conflicts = 0
        last_content: typing.List[str] = []
        for (headers, content) in self._get_file_diffs(output_split[0].decode('utf-8')):
            if len(headers) == 0:
                break

            match = GitDiff.DIFFSTART_REGEX.match(headers[0])
            if not match:
                raise ValueError(f'expected diff header, but got {headers[0]}')
            if match.groups()[0] != 'cc':
                raise ValueError(f'expected combined diff, but got {match.groups()[0]}')

            filename = headers[0][match.end():]

            results.append(GitFile(
                filename,
                None,
                None,
                None,
                headers,
                content,
            ))
            last_content = content
            merge_conflicts += 1

        if len(last_content) != 0:
            output_split[0] = last_content[-1].encode('utf-8')
            last_content.pop()

        # process numstat
        while idx < len(output_split):
            parts = output_split[idx].split(b'\t')
            idx += 1
            if len(parts) == 1:
                break

            insertions, deletions, fname = parts
            old_fname = None

            try:
                if len(fname) == 0:
                    old_fname = output_split[idx].decode('utf-8')
                    idx += 1
                    fname = output_split[idx]
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

        # process patches
        result_idx = merge_conflicts
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
        """
        Iterates and yields each git diff patch entry
        """
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
        """
        Returns the separated headers and content from the git diff patch entry
        """
        idx = start
        while idx < end:
            if GitDiff.HEADERS_REGEX.search(lines[idx]) is None:
                break
            idx += 1

        return lines[start:idx], lines[idx:end]

    async def get_statuses_async(self, files: typing.List[GitFile]) -> None:
        """
        Gets git diff status output and processes it
        """
        proc = await asyncio.create_subprocess_exec(*[
            *GitDiff.STATUS_ARGS, *self.args
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise ProcessError(stderr.decode('utf-8'))

        self._process_statuses(files, output)

    def get_statuses(self, files: typing.List[GitFile]) -> None:
        """
        Gets git diff status output and processes it
        """
        with subprocess.Popen([
            *GitDiff.STATUS_ARGS, *self.args
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            output, stderr = proc.communicate()
            if proc.returncode != 0:
                raise ProcessError(stderr.decode('utf-8'))

            self._process_statuses(files, output)

    def _process_statuses(self, files: typing.List[GitFile], output: bytes) -> None:
        """
        Processes git diff status output
        """
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
                result.append(arg)
                break
            if arg[0] == '-':
                if len(arg) > 1:
                    if arg[1] != '-':
                        idx = 1
                        while idx < len(arg) and not arg[idx] in GitDiff.WHITELIST_ARGS_SINGLE_PARAM:
                            if arg[idx] not in GitDiff.WHITELIST_ARGS_SINGLE:
                                if arg[idx] in GitDiff.BLACKLIST_ARGS_SINGLE_PARAM:
                                    self._removed_args.append('-' + arg[idx:])
                                    arg = arg[:idx]
                                else:
                                    self._removed_args.append('-' + arg[idx])
                                    arg = arg[:idx] + arg[idx + 1:]
                            else:
                                idx += 1
                        if len(arg) == 1:
                            continue
                    else:
                        if not any(arg.startswith(warg) for warg in GitDiff.WHITELIST_ARGS):
                            self._removed_args.append(arg)
                            continue
                        if arg.startswith('--src-prefix='):
                            self.src_prefix = arg[len('--src-prefix='):]
                        if arg.startswith('--dst-prefix='):
                            self.dst_prefix = arg[len('--dst-prefix='):]

            result.append(arg)

        return result

    @property
    def removed_args(self) -> typing.List[str]:
        return self._removed_args[:]

class ProcessError(Exception):
    pass
