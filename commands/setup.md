---
name: setup
description: 設定 LINE Bot token 和 webhook URL，選擇執行代理
---

# LINE Bot Setup

執行以下步驟設定 LINE Bot：

1. **詢問使用者以下資訊：**

   - **CHANNEL_ACCESS_TOKEN** (必填): LINE Bot 的 Channel Access Token
     - 取得方式：LINE Developers Console → 你的 Bot → Messaging API → Channel access token → Issue
   
   - **WEBHOOK_URL** (必填): Google Apps Script 收集訊息的網址
     - 格式：`https://script.google.com/macros/s/.../exec`
   
   - **BOT_TRIGGER** (選填): Bot 觸發詞，預設 `@mydevBot`
   
   - **POLL_INTERVAL** (選填): 輪詢間隔秒數，預設 `10`
   
   - **EXEC_TIMEOUT** (選填): 代理執行超時秒數，預設 `300`
   
   - **AGENT_TYPE** (選填): 執行代理，選項：`copilot` 或 `hermes`，預設 `copilot`
   
   - **HERMES_GATEWAY_TOKEN** (若選 hermes): Hermes Gateway Token
     - 取得方式：執行 `hermes config get gateway.token`

2. **建立 config.json：**

```bash
# 寫入設定檔
cat > .github/copilot-skills/line-bot/script/config.json << 'EOF'
{
  "CHANNEL_ACCESS_TOKEN": "<使用者輸入的 token>",
  "WEBHOOK_URL": "<使用者輸入的 URL>",
  "BOT_TRIGGER": "@mydevBot",
  "POLL_INTERVAL": 10,
  "EXEC_TIMEOUT": 300,
  "AGENT_TYPE": "copilot",
  "HERMES_GATEWAY_TOKEN": "<若使用 hermes，需提供>"
}
EOF
```

3. **驗證設定：**

```bash
# 測試抓取訊息
.venv/Scripts/python.exe .github/copilot-skills/line-bot/script/scheduler.py run

# 或在 WSL/Linux 上
python .github/copilot-skills/line-bot/script/scheduler.py run
```

4. **確認完成後回報：**

```
✅ LINE Bot 設定完成！

設定內容：
- Token: ****...**** (已隱藏)
- Webhook: https://script.google.com/...
- 觸發詞: @mydevBot
- 輪詢間隔: 10 秒
- 代理: copilot (或 hermes)

使用 /line-bot:start 啟動排程
```
