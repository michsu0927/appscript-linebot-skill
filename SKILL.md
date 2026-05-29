---
name: line-bot
description: 透過 LINE 發送指令給 Copilot CLI 或 Hermes Agent 執行，實現遠端開發對話。收到 @mydevBot 訊息後，立即回覆「執行中」，背景執行代理，完成後用 Push API 回傳結果。支援 Copilot 和 Hermes 兩種代理。
allowed-tools: Bash, Read, Write, Edit, Python
---

# LINE Bot - Multi-Agent Bridge

透過 LINE 群組發送指令，讓 Copilot CLI 或 Hermes Agent 執行並回傳結果。

## 快速開始

```bash
# 1. 設定（首次使用）
/line-bot:setup

# 2. 啟動排程
/line-bot:start

# 3. 在 LINE 發送指令
@mydevBot 告訴我現在時間
@mydevBot 建立 hello.py 印出 Hello World

# 4. 停止排程
/line-bot:stop
```

## 運作流程

```
LINE 群組: @mydevBot 建立 hello.py
        ↓
1️⃣ Reply API: "⏳ 收到，執行中..." (立即)
        ↓
2️⃣ 背景執行 Agent (Copilot 或 Hermes)
        ↓
3️⃣ Push API: 執行結果 (完成後)
```

## 指令

| 指令 | 說明 |
|------|------|
| `/line-bot:setup` | 設定 LINE Bot token 和 webhook |
| `/line-bot:start` | 啟動排程（預設每 10 秒檢查） |
| `/line-bot:start 30` | 啟動排程（每 30 秒檢查） |
| `/line-bot:stop` | 停止排程 |
| `/line-bot:status` | 查看排程狀態和最近日誌 |

## 檔案結構

```
.github/copilot-skills/line-bot/
├── SKILL.md              # 本文件
├── commands/             # Slash 指令
│   ├── setup.md
│   ├── start.md
│   ├── stop.md
│   └── status.md
├── script/
│   ├── line_bot.py       # 主邏輯（多代理支援）
│   ├── scheduler.py      # 排程器
│   ├── config.example.json
│   ├── config.json       # 你的設定（gitignore）
│   ├── linemessage.json  # 暫存訊息（gitignore）
│   └── reply.log         # 回覆記錄（gitignore）
└── reference/
    └── setup.md          # 詳細設定說明
```

## 前置需求

1. **LINE Bot** - 在 [LINE Developers Console](https://developers.line.biz/console/) 建立
2. **Google Apps Script** - 收集 LINE webhook 訊息（詳見 `reference/setup.md`）
3. **Python 環境** - 需安裝 `httpx` 和 `schedule`
4. **執行代理**（二擇一）：
   - **Copilot CLI** - GitHub Copilot CLI（Windows, 需 sandbox/bin/copilot.cmd）
   - **Hermes Agent** - Hermes Agent CLI（Linux/WSL, 自動偵測）

## 代理選擇

### 使用 Copilot（預設）

編輯 `config.json`：

```json
{
  "AGENT_TYPE": "copilot",
  ...
}
```

### 使用 Hermes Agent

編輯 `config.json`：

```json
{
  "AGENT_TYPE": "hermes",
  "HERMES_GATEWAY_TOKEN": "你的 Gateway Token",
  ...
}
```

**Hermes Gateway Token 取得：**

```bash
# 在 WSL/Linux 上
hermes config get gateway.token
```

或查看 `~/.hermes/config.yaml` 中的 `gateway.token` 欄位。

## LINE 指令範例

```
@mydevBot 告訴我現在時間
@mydevBot 列出 workspace 目錄下的檔案
@mydevBot 建立一個 Python 腳本計算 1 到 100 的總和
@mydevBot 解釋 line_bot.py 的程式碼
```

## 注意事項

- **Copilot 執行超時**：最長 5 分鐘，超時會回報
- **LINE 訊息限制**：單則訊息限制 5000 字，超過會截斷
- **Config 安全**：`config.json` 包含敏感 token，請勿 commit
- **Agent 自動偵測**：Hermes 會嘗試 CLI 優先，失敗時改用 HTTP Gateway API

## 架構改進

本版本支援多代理架構：

- **`run_copilot_cli(prompt, timeout)`** - 執行 Copilot CLI
- **`run_hermes_agent(prompt, timeout)`** - 執行 Hermes Agent（CLI 或 HTTP API）
- **`get_agent_runner(agent_type)`** - 代理分派器

新增代理時，只需新增執行函式並在 `get_agent_runner()` 中註冊。

### 未來擴展

可輕鬆支援其他代理：

```python
def run_claude_cli(prompt, timeout=300):
    # 實裝 Claude CLI 執行邏輯
    pass

def run_opencode(prompt, timeout=300):
    # 實裝 OpenCode 執行邏輯
    pass
```

然後在 `config.json` 中設定 `"AGENT_TYPE": "claude"` 或 `"opencode"` 即可。
