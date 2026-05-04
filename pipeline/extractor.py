"""
模組: Extractor
負責處理 API 請求、模擬瀏覽器行為及下載原始 PDF 檔案。

⚠️ 注意 (Note to Reviewers):
此為公開展示版本。真實環境中：
1. get_fresh_credentials() 會使用 Playwright 繞過政府網站免責聲明並攔截 Token。
2. get_daily_updated_devs() 及 fetch_detail_and_download() 會發送真實 requests，
   並利用 session_hash 下載最新 PDF 文件。
此處已替換為 Mock 邏輯以保護數據安全及避免對目標伺服器造成負擔。
"""

import time
import os
import csv
import json
import asyncio
from datetime import datetime, timedelta

# ==========================================
# 1. 輔助函數 (Utility Functions)
# ==========================================
def load_custom_names(csv_path="project_names.csv"):
    """載入自訂樓盤名稱 Mapping，若找不到則使用 API 預設名稱"""
    custom_names = {}
    try:
        # 展示處理帶有 BOM 的 CSV 檔案的嚴謹性 (utf-8-sig)
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2: 
                    custom_names[str(row[0]).strip()] = str(row[1]).strip()
        print(f"✅ 成功載入 {len(custom_names)} 個自訂樓盤名。")
    except FileNotFoundError:
        print(f"⚠️ 搵唔到 '{csv_path}'，將會使用預設樓盤名。")
    return custom_names

def send_discord_msg_in_chunks(webhook_url, message):
    """
    智能分段推送器 (Message Chunker)
    繞過 Discord API 的 2000 字元限制，確保長篇報告能完整送達。
    """
    max_length = 1900 
    lines = message.split('\n')
    current_message = ""

    print("✉️ [Notifier] 準備分段推送情報至 Discord...")
    for line in lines:
        if len(current_message) + len(line) + 1 > max_length:
            if current_message.strip():
                # 實際環境: requests.post(webhook_url, json={"content": current_message})
                print(f"   [Mock POST] 發送字節: {len(current_message)}")
                time.sleep(1) # 避免 Rate Limit
            current_message = line + "\n"
        else:
            current_message += line + "\n"

    if current_message.strip():
        # 實際環境: requests.post(...)
        print(f"   [Mock POST] 發送最後分段: {len(current_message)}")
        print("✅ 成功發送情報至 Discord！")

# ==========================================
# 2. 核心爬蟲與 API 邏輯 (Mocked for Showcase)
# ==========================================
async def get_fresh_credentials():
    """
    [🏆 核心邏輯已隱藏: Playwright 防爬蟲繞過]
    模擬無頭瀏覽器，點擊免責聲明並攔截 Authorization Header (Token), Cookies 及 SessionHash。
    """
    print("🕵️‍♂️ 1. [Mock] 派出特工前往免責聲明頁面攞通行證...")
    await asyncio.sleep(1) # 模擬網絡延遲
    print("✅ 2. [Mock] 成功偷取 Token 及 Session Hash！")
    return "mock_jwt_token", "mock_cookie_string", "mock_session_hash"

def get_daily_updated_devs(token, cookie_str, target_days=1):
    """
    [🏆 核心邏輯已隱藏: API 探索]
    掃描過去 24 小時內有上載核心文件 (SB, PL, SA, ROT) 的樓盤列表。
    """
    print(f"📡 3. [Mock] 啟動雷達：掃描過去 {target_days} 日有「成交紀錄冊」更新嘅樓盤...")
    
    # 模擬 API 回傳的 Payload 結構
    mock_dev_list_transactions = [
        {"id": "1234", "engName": "Centra Horizon", "chnName": "海日灣II"},
        {"id": "5678", "engName": "The Cullinan", "chnName": "天璽"}
    ]
    
    return [], [], [], mock_dev_list_transactions

def format_dev_list(dev_list, custom_names_dict, doc_type, doc_key=None, token=None, cookies=None, target_days=1):
    """將 API 回傳的 raw JSON 資料格式化為易讀的 Markdown 報告。"""
    if not dev_list: return "> 暫時無更新"
    
    output = [f"👉 總共有 **{len(dev_list)}** 個樓盤更新咗 {doc_type}:"]
    for dev in dev_list:
        dev_id = str(dev.get('id', ''))
        eng_name = str(dev.get('engName', '')).strip()
        chn_name = str(dev.get('chnName', '')).strip()
        
        # 匹配自訂名稱
        primary_name = custom_names_dict.get(dev_id, f"{eng_name} ({chn_name})" if eng_name and chn_name else chn_name)
        
        # 模擬獲取詳細資訊 (如更新張數)
        extra_info = " [今日上載: **1** 張]" if doc_key else ""
        output.append(f"- {primary_name} {extra_info}")
        
    return "\n".join(output)

def fetch_detail_and_download(project_id, default_name, custom_names_dict, token, cookie_str, session_hash, current_idx, total_count):
    """
    [🏆 核心邏輯已隱藏: PDF 文件下載]
    根據 Project ID 獲取最新 ROT 的 Folder ID 與 File Name，並構建 Download URL 進行下載。
    """
    final_dev_name = custom_names_dict.get(str(project_id), default_name)
    safe_dev_name = "".join([c for c in final_dev_name if c.isalpha() or c.isdigit() or c in [' ', '_', '-', '．']]).rstrip()
    
    print(f"   🚚 [Mock] 正在處理: {safe_dev_name} (ID: {project_id}) ({current_idx}/{total_count})")
    
    # 實際環境中，這裡會根據 API 回應下載 PDF 並儲存到 DOWNLOAD_FOLDER
    # 展示版直接返回本地的 sample_data 路徑
    mock_save_path = os.path.join("sample_data", f"sample_rot.pdf")
    print(f"      ✅ [Mock] 成功下載 (指向本地測試檔): {safe_dev_name}_ROT.pdf")
    
    return mock_save_path, safe_dev_name

# 若獨立運行此模組的測試邏輯
if __name__ == "__main__":
    async def test_extractor():
        custom_names = load_custom_names()
        token, cookie, session = await get_fresh_credentials()
        _, _, _, trx_list = get_daily_updated_devs(token, cookie)
        print("\n格式化結果:")
        print(format_dev_list(trx_list, custom_names, "成交紀錄冊"))
    
    asyncio.run(test_extractor())
