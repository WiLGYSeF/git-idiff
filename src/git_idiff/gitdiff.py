import asyncio
import re
import subprocess
import typing

class GitFile(typing.NamedTuple):
    filename: str
    old_filename: typing.Optional[str]
    insertions: typing.Optional[int]
    deletions: typing.Optional[int]

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

    def __init__(self, args: typing.Optional[typing.List[str]] = None):
        self.line_prefix_str: str = ''

        self.args = self._sanitize_args(args) if args is not None else []

    async def get_filenames_async(self) -> typing.List[GitFile]:
        proc = await asyncio.create_subprocess_exec(*[
            'git', 'diff', '--numstat', '-z', *self.args
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = await proc.communicate()

        return self._get_filenames(output)

    def get_filenames(self) -> typing.List[GitFile]:
        return self._get_filenames(subprocess.check_output([
            'git', 'diff', '--numstat', '-z', *self.args
        ]))

    def _get_filenames(self, output: bytes) -> typing.List[GitFile]:
        output_split = output.split(b'\0')
        idx = 0

        results: typing.List[GitFile] = []

        while idx < len(output_split):
            parts = self.noprefix(output_split[idx]).split(b'\t')
            idx += 1
            if len(parts) != 3:
                continue

            insertions, deletions, fname = parts
            oldfname = None

            if len(fname) == 0:
                oldfname = self.noprefix(output_split[idx]).decode('utf-8')
                idx += 1
                fname = self.noprefix(output_split[idx])
                idx += 1

            results.append(GitFile(
                fname.decode('utf-8'),
                oldfname,
                int(insertions) if insertions != b'-' else None,
                int(deletions) if deletions != b'-' else None
            ))

        return results

    def get_file_diff(self,fname: str) -> typing.Tuple[typing.List[str], typing.List[str]]:
        output = subprocess.check_output([
            'git', 'diff', *self.args, '--', fname
        ])
        lines = output.decode('utf-8').split('\n')

        headers_regex = re.compile(
            r'^(diff|(old|new) mode|(new|deleted) file|copy|rename|((dis)?similarity )?index|---|\+\+\+) '
        )
        headers = []

        while len(lines) > 0:
            if headers_regex.search(self.noprefix(lines[0])) is None:
                break
            headers.append(lines.pop(0))

        return headers, lines

    def _sanitize_args(self, args: typing.List[str]) -> typing.List[str]:
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
                        if arg.startswith('--line-prefix='):
                            self.line_prefix_str = arg[len('--line-prefix='):]
            result.append(arg)

        return result

    def has_prefix(self) -> bool:
        return len(self.line_prefix_str) != 0

    def noprefix(self, val: typing.AnyStr) -> typing.AnyStr:
        return val[len(self.line_prefix_str):] if len(self.line_prefix_str) != 0 else val
