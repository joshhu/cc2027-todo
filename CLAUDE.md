# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Early stage. `hello.py` is a standalone script that prints today's date with the weekday in Chinese (`python3 hello.py`). `todo.py` is the todo CLI below, tested by `test_todo.py`. Run tests with `python3 -m unittest -v`. No dependencies, build, or lint setup.

## Todo CLI (`todo.py`)

The goal is a command-line to-do list, run as `python3 todo.py <command>`, with four commands: `add`, `done`, `list`, `remove`.

Target `list` output (from the user's sketch):

```
  1. [ ] 買牛奶            到期 11/06
  2. [x] 繳電話費          到期 11/05
  3. [ ] 寫第二章          到期 11/08
```

- Completed items show `[x]`; overdue items are shown in red.
- Each task has a name, a done flag, and a due date (MM/DD). `done` and `remove` refer to tasks by the number `list` shows.
- Data must be saved to a file between runs, because each command runs as a new process.
- Task names are in Chinese. CJK characters take two terminal columns, so aligning the due-date column needs display-width handling (e.g. `unicodedata.east_asian_width`), not `len()`.

Decided rules:

- Completed items are never overdue.
- The due date is optional (`add <name> [MM/DD]`).
- MM/DD means the current year at the time of `add`; stored as a full ISO date in `todo.json` so it doesn't shift later.
- Tasks are listed in insertion order; numbers are list positions, so they renumber after `remove`.
- Data lives in `todo.json` next to `todo.py`; override with the `TODO_FILE` env var (tests use this).
- Red is only emitted when stdout is a TTY.

## Conventions

- User-facing text is in Traditional Chinese.
- Python 3 standard library only so far.
