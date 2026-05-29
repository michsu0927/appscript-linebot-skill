# -*- coding: utf-8 -*-
"""
LINE Bot Scheduler - 定期抓取 LINE 訊息並處理
"""
import httpx
import json
import os
import time
import schedule
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'linemessage.json')
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')

def load_config():
    """載入設定檔"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_webhook_url():
    """取得 Webhook URL"""
    config = load_config()
    return config.get('WEBHOOK_URL', '')

def process_and_reply(data):
    """處理訊息 - 調用 line_bot 處理"""
    from line_bot import process_messages
    process_messages()

def fetch_and_save():
    """抓取訊息並儲存"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] Fetching...')
    
    url = get_webhook_url()
    if not url or 'YOUR_' in url:
        print(f'[{ts}] ⚠️ 請在 config.json 設定 WEBHOOK_URL')
        return False
    
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            
            data = {
                'fetched_at': ts,
                'status_code': resp.status_code,
                'content_type': resp.headers.get('Content-Type', ''),
                'data': resp.json() if 'json' in resp.headers.get('Content-Type', '') else resp.text
            }
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f'[{ts}] Saved. Processing...')
            process_and_reply(data)
            return True
    except Exception as e:
        print(f'[{ts}] Error: {e}')
        return False

def list_jobs():
    """列出所有排程"""
    jobs = schedule.get_jobs()
    if not jobs:
        print('No scheduled jobs.')
    else:
        print(f'Scheduled jobs ({len(jobs)}):')
        for i, job in enumerate(jobs, 1):
            print(f'  {i}. {job}')

def clear_jobs():
    """清除所有排程"""
    schedule.clear()
    print('All jobs cleared.')

def run_scheduler():
    """執行排程迴圈"""
    print('Scheduler running. Press Ctrl+C to stop.')
    list_jobs()
    print('-' * 40)
    while True:
        schedule.run_pending()
        time.sleep(1)

def main():
    import sys
    
    if len(sys.argv) < 2:
        print('LINE Bot Scheduler')
        print('')
        print('Usage:')
        print('  python scheduler.py run                  # Single fetch')
        print('  python scheduler.py every <seconds>      # Run every N seconds')
        print('  python scheduler.py hourly               # Run every hour')
        print('  python scheduler.py daily <HH:MM>        # Run daily at time')
        print('  python scheduler.py list                 # List scheduled jobs')
        print('')
        print('Examples:')
        print('  python scheduler.py every 10             # Every 10 seconds')
        print('  python scheduler.py daily 09:00          # Daily at 9 AM')
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    # 讀取設定中的預設間隔
    config = load_config()
    default_interval = config.get('POLL_INTERVAL', 10)
    
    if cmd == 'run':
        fetch_and_save()
    
    elif cmd == 'every':
        seconds = int(sys.argv[2]) if len(sys.argv) > 2 else default_interval
        schedule.every(seconds).seconds.do(fetch_and_save)
        print(f'Scheduled: every {seconds} seconds')
        fetch_and_save()  # 立即執行一次
        run_scheduler()
    
    elif cmd == 'hourly':
        schedule.every().hour.do(fetch_and_save)
        print('Scheduled: every hour')
        fetch_and_save()
        run_scheduler()
    
    elif cmd == 'daily':
        at_time = sys.argv[2] if len(sys.argv) > 2 else '09:00'
        schedule.every().day.at(at_time).do(fetch_and_save)
        print(f'Scheduled: daily at {at_time}')
        run_scheduler()
    
    elif cmd == 'list':
        list_jobs()
    
    else:
        print(f'Unknown command: {cmd}')

if __name__ == '__main__':
    main()
