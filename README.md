# LINE Bot - Copilot CLI Bridge

透過 LINE 群組發送指令，讓 Copilot CLI 執行並回傳結果。

## 功能

- 📨 在 LINE 發送 `@mydevBot <指令>`
- ⏳ 立即回覆「執行中...」
- 🚀 背景執行 Copilot CLI
- 📤 完成後推送結果到 LINE

## 快速開始

### 1. 安裝套件

```bash
pip install -r .github/copilot-skills/line-bot/script/requirements.txt
```

### 2. 設定

```bash
# 複製設定範本
cp .github/copilot-skills/line-bot/script/config.example.json \
   .github/copilot-skills/line-bot/script/config.json
```

編輯 `config.json`：

```json
{
  "CHANNEL_ACCESS_TOKEN": "你的 LINE Bot Token",
  "WEBHOOK_URL": "https://script.google.com/macros/s/.../exec",
  "BOT_TRIGGER": "@mydevBot",
  "POLL_INTERVAL": 10,
  "EXEC_TIMEOUT": 300
}
```

### 3. 啟動

```bash
# 每 10 秒檢查一次訊息
python .github/copilot-skills/line-bot/script/scheduler.py every 10
```

### 4. 測試

在 LINE 群組發送：
```
@mydevBot 告訴我現在時間
```

## 設定說明

| 欄位 | 說明 | 必填 |
|------|------|------|
| `CHANNEL_ACCESS_TOKEN` | LINE Bot 的 Channel Access Token | ✅ |
| `WEBHOOK_URL` | Google Apps Script 收集訊息的網址 | ✅ |
| `BOT_TRIGGER` | 觸發詞，預設 `@mydevBot` | |
| `POLL_INTERVAL` | 輪詢間隔秒數，預設 `10` | |
| `EXEC_TIMEOUT` | Copilot CLI 執行超時秒數，預設 `300` | |

## 前置需求

### 1. LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 建立 Messaging API Channel
3. 取得 Channel Access Token

### 2. Google Apps Script（Webhook 中繼站）

由於此方案使用輪詢方式抓取訊息，需要一個 Google Apps Script 收集 LINE Webhook：

1. 建立 Google Sheet
2. 建立 Google Apps Script，部署為 Web App
3. 將 Web App URL 設為 LINE Webhook URL

詳細步驟請參考 [reference/setup.md](reference/setup.md)

### 3. Copilot CLI

需要已安裝並登入的 Copilot CLI：
```bash
copilot login
```

## 指令範例

```
@mydevBot 告訴我現在時間
@mydevBot 列出 workspace 目錄
@mydevBot 建立 hello.py 印出 Hello World
@mydevBot 解釋這段程式碼的功能
@mydevBot 修復 main.py 的 bug
```

## 檔案結構

```
.github/copilot-skills/line-bot/
├── README.md              # 本文件
├── SKILL.md               # Copilot Skill 定義
├── commands/              # Slash 指令
│   ├── setup.md
│   ├── start.md
│   ├── stop.md
│   └── status.md
├── reference/
│   └── setup.md           # 詳細設定指南
└── script/
    ├── requirements.txt   # Python 套件
    ├── config.example.json# 設定範本
    ├── config.json        # 你的設定（不要 commit）
    ├── line_bot.py        # 主邏輯
    ├── scheduler.py       # 排程器
    ├── linemessage.json   # 暫存訊息
    └── reply.log          # 回覆記錄
```

## 運作原理

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  LINE 群組  │────▶│  Google Apps     │────▶│  Google     │
│  @mydevBot  │     │  Script (Webhook)│     │  Sheet      │
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                    │
       ┌────────────────────────────────────────────┘
       │ 輪詢 (每 10 秒)
       ▼
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│ scheduler.py│────▶│   line_bot.py    │────▶│ Copilot CLI │
│  抓取訊息   │     │   處理指令       │     │   執行      │
└─────────────┘     └────────┬─────────┘     └──────┬──────┘
                             │                      │
                             │◀─────────────────────┘
                             │ 結果
                             ▼
                    ┌──────────────────┐
                    │  LINE Push API   │
                    │  回傳結果        │
                    └──────────────────┘
```

## 注意事項

- ⏱️ Copilot CLI 執行最長 5 分鐘，超時會回報
- 📝 LINE 單則訊息限制 5000 字，超過會截斷
- 🔒 `config.json` 包含敏感 token，請勿 commit
- 💰 LINE Push API 在免費額度內有數量限制

## 常見問題

### Q: 收到「執行中」但沒有結果？
檢查 `reply.log` 最後幾行，看是否有 `PUSH_FAIL` 錯誤。

### Q: 訊息沒有被處理？
1. 確認 `BOT_TRIGGER` 設定正確
2. 檢查 `linemessage.json` 是否有抓到訊息
3. 確認 scheduler 正在運行

### Q: Token 過期？
重新到 LINE Developers Console 取得新的 Channel Access Token。

## License

MIT
