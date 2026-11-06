import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

DEFAULT_FILE = Path(__file__).parent / "todo.json"
RED = "\033[31m"
RESET = "\033[0m"


def data_path():
    return Path(os.environ.get("TODO_FILE", DEFAULT_FILE))


def load(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save(path, tasks):
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def parse_due(text, today):
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})", text.strip())
    if not m:
        raise ValueError(f"日期格式錯誤：{text}（請用 MM/DD）")
    try:
        return date(today.year, int(m.group(1)), int(m.group(2)))
    except ValueError:
        raise ValueError(f"日期不存在：{text}") from None


def is_overdue(task, today):
    due = task.get("due")
    return not task["done"] and due is not None and date.fromisoformat(due) < today


def display_width(s):
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s)


def pad(s, width):
    return s + " " * (width - display_width(s))


def format_list(tasks, today, color=False):
    if not tasks:
        return "目前沒有待辦事項"
    num_width = len(str(len(tasks)))
    name_width = max(display_width(t["name"]) for t in tasks) + 2
    lines = []
    for i, t in enumerate(tasks, 1):
        mark = "x" if t["done"] else " "
        line = f"  {i:>{num_width}}. [{mark}] "
        if t.get("due"):
            d = date.fromisoformat(t["due"])
            line += f"{pad(t['name'], name_width)}到期 {d.month:02}/{d.day:02}"
        else:
            line += t["name"]
        if color and is_overdue(t, today):
            line = f"{RED}{line}{RESET}"
        lines.append(line)
    return "\n".join(lines)


def _index(tasks, number):
    if not 1 <= number <= len(tasks):
        raise ValueError(f"沒有第 {number} 項")
    return number - 1


def add(tasks, name, due=None):
    task = {"name": name, "done": False, "due": due.isoformat() if due else None}
    tasks.append(task)
    return task


def done(tasks, number):
    task = tasks[_index(tasks, number)]
    task["done"] = True
    return task


def remove(tasks, number):
    return tasks.pop(_index(tasks, number))


def clear(tasks):
    before = len(tasks)
    tasks[:] = [t for t in tasks if not t["done"]]
    return before - len(tasks)


def build_parser():
    parser = argparse.ArgumentParser(prog="todo.py", description="命令列待辦清單")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add", help="新增待辦事項")
    p.add_argument("name", help="事項名稱")
    p.add_argument("due", nargs="?", help="到期日 MM/DD（可省略）")
    sub.add_parser("list", help="列出待辦事項")
    p = sub.add_parser("done", help="標記為完成")
    p.add_argument("number", type=int, help="list 顯示的編號")
    p = sub.add_parser("remove", help="刪除待辦事項")
    p.add_argument("number", type=int, help="list 顯示的編號")
    sub.add_parser("clear", help="刪除所有已完成的事項")
    return parser


def main(argv=None, today=None):
    args = build_parser().parse_args(argv)
    today = today or date.today()
    path = data_path()
    tasks = load(path)
    try:
        if args.command == "add":
            due = parse_due(args.due, today) if args.due else None
            task = add(tasks, args.name, due)
            print(f"已新增：{task['name']}")
        elif args.command == "list":
            print(format_list(tasks, today, color=sys.stdout.isatty()))
            return 0
        elif args.command == "done":
            print(f"已完成：{done(tasks, args.number)['name']}")
        elif args.command == "remove":
            print(f"已刪除：{remove(tasks, args.number)['name']}")
        elif args.command == "clear":
            count = clear(tasks)
            if not count:
                print("沒有已完成的事項")
                return 0
            print(f"已清除 {count} 項已完成事項")
    except ValueError as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 1
    save(path, tasks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
