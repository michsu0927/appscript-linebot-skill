#!/usr/bin/env python3
"""
LINE Bot - Multi-Agent Bridge (Copilot + Hermes)
透過 LINE 發送指令給 Copilot CLI 或 Hermes Agent 執行，結果用 Push API 回傳
"""
import json
import httpx
import subprocess
import threading
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
MESSAGE_FILE = SCRIPT_DIR / "linemessage.json"
REPLY_LOG = SCRIPT_DIR / "reply.log"
CONFIG_FILE = SCRIPT_DIR / "config.json"

def load_config():
    """載入設定檔"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_replied_ids():
    """讀取已回覆的 message IDs"""
    if not REPLY_LOG.exists():
        return set()
    with open(REPLY_LOG, "r", encoding="utf-8") as f:
        return set(line.split("|")[0].strip() for line in f if line.strip())

def log_reply(message_id, text, status):
    """記錄回覆結果"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(REPLY_LOG, "a", encoding="utf-8") as f:
        f.write(f"{message_id}|{timestamp}|{status}|{text}\n")

def reply_message(reply_token, message, access_token):
    """呼叫 LINE Reply API（需 30 秒內）"""
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message[:5000]}]
    }
    
    with httpx.Client() as client:
        resp = client.post(url, headers=headers, json=payload)
        return resp.status_code, resp.text

def push_message(to, message, access_token):
    """呼叫 LINE Push API（無時間限制）"""
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    # LINE 單則訊息限制 5000 字
    text = message[:4950] + "\n...(truncated)" if len(message) > 5000 else message
    payload = {
        "to": to,
        "messages": [{"type": "text", "text": text}]
    }
    
    with httpx.Client() as client:
        resp = client.post(url, headers=headers, json=payload)
        return resp.status_code, resp.text

# ==================== Agent Runners ====================

def run_copilot_cli(prompt, timeout=300):
    """執行 Copilot CLI 並回傳結果"""
    try:
        result = subprocess.run(
            ["copilot", "-p", prompt, "--allow-all", "-s"],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        
        output = result.stdout or ""
        if result.stderr:
            output += f"\n\n[stderr]\n{result.stderr}"
        
        return output.strip() if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return f"⏱️ 執行超時 (>{timeout}秒)"
    except FileNotFoundError:
        return "❌ Copilot CLI 未找到 (copilot.cmd 不在 PATH)"
    except Exception as e:
        return f"❌ 執行錯誤: {str(e)}"

def run_hermes_agent(prompt, timeout=300):
    """
    執行 Hermes Agent 並回傳結果
    
    支援兩種模式：
    1. 如果有 hermes CLI，直接呼叫
    2. 否則透過 HTTP 呼叫 Gateway API
    """
    try:
        # 方法 1：直接用 hermes CLI (使用 chat 命令)
        result = subprocess.run(
            ["hermes", "chat", "-q", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        
        output = result.stdout or ""
        if result.stderr:
            output += f"\n\n[stderr]\n{result.stderr}"
        
        return output.strip() if output.strip() else "(no output)"
    except FileNotFoundError:
        # 方法 2：嘗試 HTTP Gateway API
        try:
            gateway_url = "http://127.0.0.1:18789/api/chat"
            config = load_config()
            gateway_token = config.get("HERMES_GATEWAY_TOKEN", "")
            
            if not gateway_token:
                return "❌ Hermes Gateway Token 未配置 (設定 HERMES_GATEWAY_TOKEN)"
            
            headers = {
                "Authorization": f"Bearer {gateway_token}",
                "Content-Type": "application/json"
            }
            payload = {"message": prompt}
            
            with httpx.Client() as client:
                resp = client.post(gateway_url, headers=headers, json=payload, timeout=timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("response", "(no response)")
                else:
                    return f"❌ Gateway 錯誤: {resp.status_code}"
        except Exception as e:
            return f"❌ Gateway 連接失敗: {str(e)}"
    except subprocess.TimeoutExpired:
        return f"⏱️ 執行超時 (>{timeout}秒)"
    except Exception as e:
        return f"❌ 執行錯誤: {str(e)}"

def get_agent_runner(agent_type):
    """根據 agent_type 回傳對應的執行函式"""
    runners = {
        "copilot": run_copilot_cli,
        "hermes": run_hermes_agent,
    }
    return runners.get(agent_type.lower(), run_copilot_cli)  # 預設用 Copilot

# ==================== Message Processing ====================

def clean_hermes_output(text):
    """清理 Hermes 的格式化輸出（移除框線、分隔符等）"""
    lines = text.split('\n')
    cleaned = []
    skip_next = False
    
    for line in lines:
        # 移除各種框線和分隔符
        if any(x in line for x in ['╭─', '╰──', '┊ ', '────────', '═════', '───────']):
            continue
        # 移除 "Resume this session" 及其後續的資訊
        if 'Resume this session' in line or 'Session:' in line or 'Duration:' in line or 'Messages:' in line:
            skip_next = True
            continue
        if skip_next and line.strip() == '':
            skip_next = False
        if skip_next:
            continue
        # 移除 "Initializing agent..." 等初始化訊息
        if any(x in line for x in ['Initializing agent', 'Query:', 'preparing terminal']):
            continue
        # 保留其他行
        if line.strip():
            cleaned.append(line)
    
    result = '\n'.join(cleaned).strip()
    return result if result else "(無回應)"

def process_command_async(msg_id, command, target_id, access_token, timeout, agent_type):
    """背景執行 Agent 並推送結果"""
    print(f"  🚀 開始執行 ({agent_type}): {command}")
    
    runner = get_agent_runner(agent_type)
    result = runner(command, timeout)
    
    # 清理輸出格式
    clean_result = clean_hermes_output(result)
    
    print(f"  📤 推送結果到 LINE...")
    response = f"💬 {command}\n\n{clean_result}"
    status_code, _ = push_message(target_id, response, access_token)
    
    status = "PUSH_OK" if status_code == 200 else f"PUSH_FAIL:{status_code}"
    log_reply(f"{msg_id}_push", command, status)
    print(f"  {'✅' if status_code == 200 else '❌'} Push: {status_code}")

def process_messages():
    """處理 linemessage.json 中的訊息"""
    config = load_config()
    access_token = config.get("CHANNEL_ACCESS_TOKEN", "")
    bot_trigger = config.get("BOT_TRIGGER", "@mydevBot")
    exec_timeout = config.get("EXEC_TIMEOUT", 300)
    agent_type = config.get("AGENT_TYPE", "copilot")  # 預設 copilot
    
    if not access_token or "YOUR_" in access_token:
        print("⚠️ 請在 config.json 設定 CHANNEL_ACCESS_TOKEN")
        return
    
    if not MESSAGE_FILE.exists():
        print(f"⚠️ 找不到 {MESSAGE_FILE}")
        return
    
    with open(MESSAGE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    replied_ids = get_replied_ids()
    items = data.get("data", [])
    
    for item in items:
        payload = item.get("Full JSON Payload", {})
        # 處理 payload 是空字符串或非字典的情況
        if isinstance(payload, str):
            if not payload or payload.strip() == "":
                continue  # 跳過空的 payload
            try:
                payload = json.loads(payload)
            except:
                continue
        if not isinstance(payload, dict):
            continue
        events = payload.get("events", [])
        
        for event in events:
            if event.get("type") != "message":
                continue
            
            msg = event.get("message", {})
            msg_id = msg.get("id", "")
            msg_text = msg.get("text", "").strip()
            reply_token = event.get("replyToken", "")
            source = event.get("source", {})
            target_id = source.get("groupId") or source.get("userId", "")
            
            # 跳過已回覆的訊息
            if msg_id in replied_ids:
                continue
            
            # 檢查是否包含觸發詞
            if bot_trigger not in msg_text:
                continue
            
            # 取得指令（移除觸發詞）
            command = msg_text.replace(bot_trigger, "").strip()
            
            if not command:
                reply_message(reply_token, f"請輸入指令，例如：\n{bot_trigger} 建立 hello.py 印出 Hello World", access_token)
                log_reply(msg_id, "(empty)", "SKIP")
                continue
            
            print(f"📨 收到指令: {command}")
            
            # 1. 立即回覆「執行中」
            reply_status, _ = reply_message(
                reply_token, 
                f"⏳ 收到，執行中...\n\n> {command}", 
                access_token
            )
            log_reply(msg_id, command, f"REPLY:{reply_status}")
            
            # 2. 背景執行 Agent 並推送結果
            thread = threading.Thread(
                target=process_command_async,
                args=(msg_id, command, target_id, access_token, exec_timeout, agent_type),
                daemon=True
            )
            thread.start()

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 檢查訊息...")
    process_messages()

if __name__ == "__main__":
    main()
