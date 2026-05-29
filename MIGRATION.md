# LINE Bot 多代理支援 - 改動說明

## 版本

- **原始版本**：Copilot CLI 專用
- **改寫版本**：Copilot + Hermes Agent 多代理支援

## 核心改動

### 1. line_bot.py

#### 新增多代理支援機制

**原始版本：**
```python
def run_copilot_cli(prompt, timeout=300):
    # 只支援 Copilot
```

**改寫版本：**
```python
def run_copilot_cli(prompt, timeout=300):
    # Copilot 執行邏輯

def run_hermes_agent(prompt, timeout=300):
    # Hermes 執行邏輯（支援 CLI 或 HTTP Gateway API）

def get_agent_runner(agent_type):
    # 根據 agent_type 回傳對應的執行函式
```

#### process_command_async() 改動

**原始版本：**
```python
def process_command_async(msg_id, command, target_id, access_token, timeout):
    result = run_copilot_cli(command, timeout)  # 硬寫 Copilot
```

**改寫版本：**
```python
def process_command_async(msg_id, command, target_id, access_token, timeout, agent_type):
    runner = get_agent_runner(agent_type)
    result = runner(command, timeout)  # 動態選擇代理
```

#### process_messages() 改動

**原始版本：**
```python
agent_type = "copilot"  # 硬寫
```

**改寫版本：**
```python
agent_type = config.get("AGENT_TYPE", "copilot")  # 從 config 讀取
```

### 2. config.example.json

新增兩個欄位：

```json
{
  ...原有欄位...,
  "AGENT_TYPE": "copilot",                         // 新增：執行代理選擇
  "HERMES_GATEWAY_TOKEN": "YOUR_TOKEN_HERE"       // 新增：Hermes Gateway Token
}
```

### 3. SKILL.md

- 新增「代理選擇」章節
- 新增「架構改進」和「未來擴展」說明
- 更新前置需求，列出支援的代理

### 4. commands/setup.md

- 新增 AGENT_TYPE 和 HERMES_GATEWAY_TOKEN 設定提示
- 新增 Hermes Gateway Token 取得方式說明

## 使用方式

### 切換到 Hermes

1. 取得 Hermes Gateway Token：
```bash
hermes config get gateway.token
```

2. 編輯 config.json：
```json
{
  "AGENT_TYPE": "hermes",
  "HERMES_GATEWAY_TOKEN": "你的 token"
}
```

3. 重啟排程即可生效

### 切換回 Copilot

編輯 config.json：
```json
{
  "AGENT_TYPE": "copilot"
}
```

## 向後相容性

✅ **完全向後相容**

- 若 `AGENT_TYPE` 未設定，預設使用 Copilot
- 現有的 config.json 無需修改
- Copilot 執行邏輯完全相同

## 未來擴展

增加新代理非常簡單：

1. 新增執行函式：
```python
def run_new_agent(prompt, timeout=300):
    # 實裝新代理執行邏輯
    pass
```

2. 在 `get_agent_runner()` 中註冊：
```python
runners = {
    "copilot": run_copilot_cli,
    "hermes": run_hermes_agent,
    "new-agent": run_new_agent,  // 新增這行
}
```

3. 在 config.json 中設定即可使用：
```json
{
  "AGENT_TYPE": "new-agent"
}
```

## 測試

建議測試流程：

1. **Copilot 測試**（現有功能不變）：
```bash
python scheduler.py run
```

2. **Hermes 測試**（新功能）：
```bash
# 先確保 Hermes Gateway 運行
hermes gateway status

# 設定 config.json 的 AGENT_TYPE 為 hermes
# 然後執行
python scheduler.py run
```

## 備註

- `run_hermes_agent()` 支援兩種模式：
  1. **CLI 模式**：若 `hermes` 在 PATH，直接呼叫 `hermes chat -q` 指令
  2. **HTTP 模式**：若 CLI 不可用，透過 HTTP 呼叫 Gateway API
  
  這樣可以在 Windows (Copilot) 和 WSL/Linux (Hermes) 上自動選擇正確的執行方式。

- 若 Hermes Gateway Token 缺失或無效，會回傳錯誤訊息指引設定

## 最新改動 (2026-05-29)

### 1. 輸出格式最佳化

新增 `clean_hermes_output()` 函數移除冗長的格式化輸出：

- ✅ 移除 Hermes 的 TUI 框線（╭─、╰──、┊ 等）
- ✅ 移除分隔符（────────、═════ 等）
- ✅ 移除初始化訊息（Initializing agent, Query:, preparing terminal）
- ✅ 移除 Session 信息和 Resume 指引
- ✅ 只保留實質的執行結果和回應

**修改位置：** `line_bot.py` 第 162-189 行

**效果：**
- **之前：** 冗長的框線和 Hermes 內部訊息混在一起
- **之後：** 清潔簡潔的執行結果，適合 LINE 群組討論

### 2. 回應格式簡化

修改 `process_command_async()` 的回應格式：

**之前：**
```
📋 執行完成 [hermes]

> 告訴我現在時間

Query: 告訴我現在時間
（大量框線和訊息）
```

**之後：**
```
💬 告訴我現在時間

（清理後的執行結果）
```

### 3. Webhook Payload 容錯處理

修復新 Google Apps Script webhook 可能返回空字符串 payload 的問題：

**修改位置：** `line_bot.py` 第 200-210 行

**邏輯：**
```python
if isinstance(payload, str):
    if not payload or payload.strip() == "":
        continue  # 跳過空的 payload
    try:
        payload = json.loads(payload)  # 若是 JSON 字符串則解析
    except:
        continue
if not isinstance(payload, dict):
    continue  # 只處理字典型的 payload
```

這確保即使 webhook 返回混合格式的資料也能正確處理。

### 4. Webhook URL 更新

支援更新 `config.json` 的 `WEBHOOK_URL` 欄位指向新的 Google Apps Script。

**使用方式：**
編輯 `config.json`，修改 `WEBHOOK_URL` 欄位即可在不重寫代碼的情況下切換 webhook 來源。
