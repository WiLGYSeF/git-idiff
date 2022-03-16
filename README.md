# git-idiff

An interactive curses tool for viewing git diffs that span multiple files.

![git idiff](/docs/images/git-idiff.png)

# Usage

Run git-idiff in a git directory to get an interactive view of the current git diff.

## Using Diff Arguments

git-idiff takes any arguments recognized by the `git diff` command and will use them when displaying output.

Using:

```bash
git-idiff HEAD~2 -R -U5
```

will display the same output that `git diff` displays, but in an interactive view.

# Keys

| Key | Description |
|---|---|
| Arrow keys | Scroll diff contents |
| Page up/down | Scroll diff contents one page up/down |
| Home/end | Scroll to start/end of diff contents |
| `n` | Select next file |
| `p` | Select previous file |
| `f` | Toggle filelist pane |
| `?` | Show help menu |
| `q` | Quit |

git-idiff also supports mouse control.

| Mouse Action | Description |
|---|---|
| Scroll (on diff pane) | Scroll diff contents |


Actions when the mouse is in the filelist pane:

| Mouse Action | Description |
|---|---|
| Click | Select file clicked |
| Scroll | Select previous/next file |
| Drag (on filelist pane border) | Resize filelist pane |

# Filelist Pane

![filelist pane](/docs/images/filelist.png)

The filelist pane shows all files in the git diff.

Each entry begins with the file's status, number of insertions, and number of deletions, followed by the filename.

If a filename is too long, it will be truncated to fit the pane and prefixed with `##`.

The filelist pane can be resized by dragging the filelist pane border with the mouse.
