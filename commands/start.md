---
name: start
description: 啟動 LINE Bot 排程
---

# 啟動 LINE Bot 排程

1. **檢查 config.json 是否存在：**

```bash
if (Test-Path ".github/copilot-skills/line-bot/script/config.json") { "OK" } else { "NOT FOUND" }
```

如果不存在，提示使用者先執行 `/line-bot:setup`

2. **讀取設定取得輪詢間隔：**

```bash
Get-Content .github/copilot-skills/line-bot/script/config.json | ConvertFrom-Json | Select-Object -ExpandProperty POLL_INTERVAL
```

3. **啟動排程（async 模式）：**

如果使用者有指定間隔秒數（如 `/line-bot:start 30`），使用該值；否則使用 config 中的 POLL_INTERVAL。

```bash
.venv\Scripts\python.exe .github\copilot-skills\line-bot\script\scheduler.py every <秒數>
```

使用 shellId: `line-bot-scheduler`

4. **確認啟動後回報：**

```
✅ LINE Bot 排程已啟動！

- 輪詢間隔: 每 10 秒
- 觸發詞: @mydevBot
- 狀態: 運行中

在 LINE 發送 @mydevBot <指令> 測試
使用 /line-bot:stop 停止排程
```
