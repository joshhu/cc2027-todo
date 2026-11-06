import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

import todo

TODAY = date(2026, 11, 5)


def task(name, done=False, due=None):
    return {"name": name, "done": done, "due": due}


class TestParseDue(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(todo.parse_due("11/06", TODAY), date(2026, 11, 6))
        self.assertEqual(todo.parse_due("1/5", TODAY), date(2026, 1, 5))

    def test_uses_current_year(self):
        self.assertEqual(todo.parse_due("03/01", date(2030, 6, 1)), date(2030, 3, 1))

    def test_invalid(self):
        for text in ["13/01", "02/30", "abc", "11-06", "2026/11/06"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                todo.parse_due(text, TODAY)


class TestDisplayWidth(unittest.TestCase):
    def test_widths(self):
        self.assertEqual(todo.display_width("abc"), 3)
        self.assertEqual(todo.display_width("買牛奶"), 6)
        self.assertEqual(todo.display_width("寫第2章"), 7)

    def test_pad(self):
        self.assertEqual(todo.display_width(todo.pad("買牛奶", 10)), 10)


class TestIsOverdue(unittest.TestCase):
    def test_cases(self):
        self.assertTrue(todo.is_overdue(task("a", due="2026-11-04"), TODAY))
        self.assertFalse(todo.is_overdue(task("a", True, "2026-11-04"), TODAY))
        self.assertFalse(todo.is_overdue(task("a", due="2026-11-05"), TODAY))
        self.assertFalse(todo.is_overdue(task("a"), TODAY))


class TestFormatList(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            task("買牛奶", due="2026-11-06"),
            task("繳電話費", True, "2026-11-01"),
            task("寫第二章", due="2026-11-01"),
            task("call mom"),
        ]

    def test_layout(self):
        lines = todo.format_list(self.tasks, TODAY).splitlines()
        self.assertEqual(lines[0], "  1. [ ] 買牛奶    到期 11/06")
        self.assertEqual(lines[1], "  2. [x] 繳電話費  到期 11/01")
        self.assertEqual(lines[3], "  4. [ ] call mom")

    def test_due_column_aligned(self):
        lines = todo.format_list(self.tasks, TODAY).splitlines()[:3]
        cols = {todo.display_width(l[: l.index("到期")]) for l in lines}
        self.assertEqual(len(cols), 1)

    def test_color(self):
        lines = todo.format_list(self.tasks, TODAY, color=True).splitlines()
        self.assertNotIn(todo.RED, lines[0])
        self.assertNotIn(todo.RED, lines[1])  # 已完成不算過期
        self.assertTrue(lines[2].startswith(todo.RED) and lines[2].endswith(todo.RESET))
        self.assertNotIn(todo.RED, todo.format_list(self.tasks, TODAY, color=False))

    def test_number_alignment(self):
        lines = todo.format_list([task(str(i)) for i in range(10)], TODAY).splitlines()
        self.assertTrue(lines[0].startswith("   1. "))
        self.assertTrue(lines[9].startswith("  10. "))

    def test_empty(self):
        self.assertEqual(todo.format_list([], TODAY), "目前沒有待辦事項")


class TestOperations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "todo.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_load_missing_file(self):
        self.assertEqual(todo.load(self.path), [])

    def test_roundtrip(self):
        tasks = []
        todo.add(tasks, "買牛奶", date(2026, 11, 6))
        todo.add(tasks, "寫報告")
        todo.done(tasks, 2)
        todo.save(self.path, tasks)
        self.assertEqual(
            todo.load(self.path),
            [task("買牛奶", due="2026-11-06"), task("寫報告", True)],
        )
        self.assertIn("買牛奶", self.path.read_text(encoding="utf-8"))

    def test_remove_renumbers(self):
        tasks = [task("a"), task("b"), task("c")]
        self.assertEqual(todo.remove(tasks, 2)["name"], "b")
        self.assertEqual([t["name"] for t in tasks], ["a", "c"])
        todo.done(tasks, 2)
        self.assertTrue(tasks[1]["done"])

    def test_clear(self):
        tasks = [task("a", True), task("b"), task("c", True), task("d")]
        self.assertEqual(todo.clear(tasks), 2)
        self.assertEqual([t["name"] for t in tasks], ["b", "d"])
        self.assertEqual(todo.clear(tasks), 0)
        self.assertEqual([t["name"] for t in tasks], ["b", "d"])

    def test_out_of_range(self):
        tasks = [task("a")]
        for n in [0, 2, -1]:
            with self.subTest(n=n):
                with self.assertRaises(ValueError):
                    todo.done(tasks, n)
                with self.assertRaises(ValueError):
                    todo.remove(tasks, n)


class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "todo.json"
        patcher = mock.patch.dict(os.environ, {"TODO_FILE": str(self.path)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def run_cmd(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = todo.main(list(argv), today=TODAY)
        return code, out.getvalue(), err.getvalue()

    def test_full_flow(self):
        self.assertEqual(self.run_cmd("add", "買牛奶", "11/06")[:2], (0, "已新增：買牛奶\n"))
        self.run_cmd("add", "繳電話費", "11/05")
        self.run_cmd("add", "寫第二章")
        self.assertEqual(self.run_cmd("done", "2")[1], "已完成：繳電話費\n")
        self.assertEqual(self.run_cmd("remove", "1")[1], "已刪除：買牛奶\n")
        code, out, _ = self.run_cmd("list")
        self.assertEqual(code, 0)
        self.assertEqual(
            out.splitlines(),
            ["  1. [x] 繳電話費  到期 11/05", "  2. [ ] 寫第二章"],
        )

    def test_clear(self):
        self.assertEqual(self.run_cmd("clear")[:2], (0, "沒有已完成的事項\n"))
        self.assertFalse(self.path.exists())
        for name in ["買牛奶", "繳電話費", "寫第二章"]:
            self.run_cmd("add", name)
        self.run_cmd("done", "1")
        self.run_cmd("done", "3")
        self.assertEqual(self.run_cmd("clear")[:2], (0, "已清除 2 項已完成事項，剩下 1 項\n"))
        self.assertEqual(self.run_cmd("list")[1], "  1. [ ] 繳電話費\n")
        self.assertEqual(self.run_cmd("clear")[1], "沒有已完成的事項\n")

    def test_errors(self):
        code, out, err = self.run_cmd("add", "x", "13/40")
        self.assertEqual(code, 1)
        self.assertIn("錯誤", err)
        self.assertFalse(self.path.exists())
        code, _, err = self.run_cmd("done", "1")
        self.assertEqual(code, 1)
        self.assertIn("沒有第 1 項", err)


if __name__ == "__main__":
    unittest.main()
