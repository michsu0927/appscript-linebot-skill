# LINE Bot 設定指南

## 1. 建立 LINE Bot

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 建立新的 Provider（或使用現有的）
3. 建立新的 **Messaging API Channel**
4. 記下以下資訊：
   - **Channel ID**
   - **Channel Secret**

## 2. 取得 Channel Access Token

1. 在 Channel 設定頁面，點選 **Messaging API** 頁籤
2. 滾動到 **Channel access token** 區域
3. 點選 **Issue** 產生 token
4. 複製 token（這是 `CHANNEL_ACCESS_TOKEN`）

## 3. 設定 Google Apps Script（收集 Webhook）

由於 LINE Webhook 需要即時回應，我們使用 Google Apps Script 作為中繼站收集訊息。

### 建立 Google Apps Script

1. 前往 [Google Apps Script](https://script.google.com/)
2. 建立新專案
3. 貼上以下程式碼：

```javascript
// Google Apps Script - LINE Webhook Collector

const SHEET_ID = 'YOUR_GOOGLE_SHEET_ID'; // 建立一個 Google Sheet 並貼上 ID

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.openById(SHEET_ID).getActiveSheet();
    
    sheet.appendRow([
      new Date().toISOString(),
      JSON.stringify(data)
    ]);
    
    return ContentService.createTextOutput(JSON.stringify({status: 'ok'}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({error: error.message}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  try {
    const sheet = SpreadsheetApp.openById(SHEET_ID).getActiveSheet();
    const data = sheet.getDataRange().getValues();
    
    // 取最新 20 筆
    const recent = data.slice(-20).map(row => ({
      'Timestamp': row[0],
      'Full JSON Payload': JSON.parse(row[1] || '{}')
    }));
    
    return ContentService.createTextOutput(JSON.stringify(recent))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({error: error.message}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
```

4. 部署為 Web App：
   - 點選 **Deploy** → **New deployment**
   - Type: **Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
   - 點選 **Deploy**
   - 複製 Web app URL（這是 `WEBHOOK_URL`）

### 設定 LINE Webhook

1. 回到 LINE Developers Console
2. 在 Messaging API 頁籤找到 **Webhook settings**
3. 貼上 Google Apps Script 的 URL
4. 開啟 **Use webhook**
5. 點選 **Verify** 測試

## 4. 建立 config.json

```bash
cp .github/copilot-skills/line-bot/script/config.example.json \
   .github/copilot-skills/line-bot/script/config.json
```

編輯 `config.json`：

```json
{
  "CHANNEL_ACCESS_TOKEN": "你的 token",
  "WEBHOOK_URL": "https://script.google.com/macros/s/.../exec",
  "BOT_TRIGGER": "@mydevBot",
  "POLL_INTERVAL": 10,
  "EXEC_TIMEOUT": 300
}
```

## 5. 測試

```bash
# 執行一次測試
.venv\Scripts\python.exe .github\copilot-skills\line-bot\script\scheduler.py run

# 啟動排程
.venv\Scripts\python.exe .github\copilot-skills\line-bot\script\scheduler.py every 10
```

在 LINE 群組發送 `@mydevBot hello` 測試。

## 注意事項

- **Token 安全**：`config.json` 已加入 `.gitignore`，請勿 commit
- **Reply Token 時效**：LINE 的 replyToken 只有約 30 秒有效，所以我們用 Push API 發送結果
- **Push API 費用**：Push API 在免費額度內有數量限制，請注意用量
