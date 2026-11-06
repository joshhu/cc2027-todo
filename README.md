# cc2027-todo

《Coding Agent 重磅出擊 - Claude Code 2027 大神培養》第 8 章（網頁版 Claude Code）的範例專案：一個命令列待辦清單，只用 Python 標準函式庫。

## 使用方式

```bash
python3 todo.py add 買牛奶 11/06
python3 todo.py list
python3 todo.py done 1
python3 todo.py remove 1
```

資料存在 `todo.py` 旁邊的 `todo.json`，可以用環境變數 `TODO_FILE` 改位置。

## 測試

```bash
python3 -m unittest -v
```

GitHub Actions 會在每次 push 與 pull request 執行同一組測試。

## 授權

MIT
