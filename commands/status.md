---
name: status
description: 查看 LINE Bot 排程狀態
---

# 查看 LINE Bot 狀態

1. **檢查排程是否運行：**

使用 `list_powershell` 查看 shellId 為 `line-bot-scheduler` 的 session 狀態

2. **讀取最近的 reply.log：**

```bash
Get-Content .github/copilot-skills/line-bot/script/reply.log -Tail 10
```

3. **讀取最近抓取的訊息：**

```bash
Get-Content .github/copilot-skills/line-bot/script/linemessage.json | ConvertFrom-Json | Select-Object -ExpandProperty fetched_at
```

4. **回報狀態：**

```
📊 LINE Bot 狀態

排程: ✅ 運行中 / ❌ 已停止
最後抓取: 2026-05-28 16:45:00

最近 5 筆處理記錄:
| 訊息 ID | 時間 | 狀態 | 指令 |
|---------|------|------|------|
| 615930064... | 16:43:55 | OK | 告訴我現在時間 |
| ... | ... | ... | ... |
```
