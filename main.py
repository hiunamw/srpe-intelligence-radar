"""
📊 SRPE Intelligence Radar & ETL Pipeline
=========================================================
角色: Orchestrator (主控台)
描述: 協調 Extractor (獲取/爬蟲), Transformer (清洗), Loader (載入) 模組，
      執行每日香港一手住宅物業市場數據的端到端 (End-to-End) 自動化處理。

⚠️ 注意 (Note to Reviewers): 
此為公開展示版本 (Showcase Version)。
為確保能在無真實數據庫憑證下運行，請搭配模組內的 [Mock 模式] 進行測試。
可將 SKIP_DOWNLOAD 設為 True，以直接測試本地 sample_data 的 PDF 清洗能力。
=========================================================
"""

import os
import time
import asyncio
import pandas as pd
from datetime import datetime, timedelta

# 引入自訂 ETL 模組
from pipeline import extractor
from pipeline import transformer
from pipeline import loader

async def main():
    try:
        # ==========================================
        # ⚙️ 系統設定與環境控制
        # ==========================================
        # 🌟 開關掣：設為 True 可跳過網絡請求，直接讀取本地 PDF 測試清洗邏輯 (方便 Unit Test)
        SKIP_DOWNLOAD = False
        
        downloaded_files = []
        custom_names_dict = extractor.load_custom_names()

        # ==========================================
        # 🕵️ 1. Extract (抽取階段：API 攔截與報告生成)
        # ==========================================
        if SKIP_DOWNLOAD:
            print("\n⏭️ [測試模式] 跳過雷達下載階段，直接讀取本地 'sample_data'...")
            # 模擬已下載的文件
            downloaded_files.append(("sample_data/sample_rot.pdf", "Demo_Project"))
        else:
            # 1.1 偵察兵出動 (獲取 Token & 生成情報報告)
            token, cookies, session_hash = await extractor.get_fresh_credentials()
            TARGET_DAYS = 1
            sb_list, pl_list, sa_list, rot_list = extractor.get_daily_updated_devs(token, cookies, target_days=TARGET_DAYS)

            print("\n🔍 正在分析數據細節 (這需要一點時間)...\n")
            yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            # 構建 Markdown 格式的情報報告
            report_lines = [
                f"**📊 SRPE 每日情報摘要 ({yesterday_str}) 📊**", "="*40,
                "**📘 售樓說明書 (Sales Brochure) 更新：**", 
                extractor.format_dev_list(sb_list, custom_names_dict, "SB", target_days=TARGET_DAYS),
                "\n**💵 價單 (Price List) 更新：**", 
                extractor.format_dev_list(pl_list, custom_names_dict, "PL", doc_key="prices", token=token, cookies=cookies, target_days=TARGET_DAYS),
                "\n**📅 銷售安排 (Sales Arrangement) 更新：**", 
                extractor.format_dev_list(sa_list, custom_names_dict, "SA", doc_key="salesArrangements", token=token, cookies=cookies, target_days=TARGET_DAYS),
                "\n**🤝 成交記錄冊 (Register of Transactions) 更新：**", 
                extractor.format_dev_list(rot_list, custom_names_dict, "ROT", target_days=TARGET_DAYS),
                "="*40
            ]
            final_report = "\n".join(report_lines)
            print(final_report)

            # 觸發 Discord 推送
            DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
            if DISCORD_WEBHOOK_URL:
                extractor.send_discord_msg_in_chunks(DISCORD_WEBHOOK_URL, final_report)
            else:
                print("⚠️ [Mock 模式] 搵唔到 Discord Webhook URL 環境變數，僅在終端機印出報告。")

            # 1.2 數據收割隊出動 (精準下載 ROT PDF)
            if not rot_list:
                print(f"\n🎉 過去 {TARGET_DAYS} 日內無任何成交紀錄冊更新。任務完成！")
                return

            print(f"\n🎯 發現 {len(rot_list)} 個 ROT 目標，準備下載...")
            for i, dev in enumerate(rot_list, start=1):
                project_id = dev.get('id')
                default_name = dev.get('engName') or dev.get('chnName') or 'Unknown'
                if project_id:
                    pdf_path, project_name = extractor.fetch_detail_and_download(
                        project_id, default_name, custom_names_dict, token, cookies, session_hash, i, len(rot_list)
                    )
                    if pdf_path: 
                        downloaded_files.append((pdf_path, project_name))

        # ==========================================
        # 🤖 2. Transform (轉換階段：非結構化 PDF -> 結構化 DataFrame)
        # ==========================================
        print(f"\n🧠 準備啟動清洗引擎！共有 {len(downloaded_files)} 份 PDF 需要處理...")
        all_dfs = []
        for pdf_path, project_name in downloaded_files:
            cleaned_df = transformer.process_single_rot(pdf_path, project_name)
            if cleaned_df is not None and not cleaned_df.empty:
                all_dfs.append(cleaned_df)
                print(f"      ✅ {project_name} 清洗完畢，搵到 {len(cleaned_df)} 筆紀錄！")

        # ==========================================
        # 🗄️ 3. Load (載入階段：本地備份與雲端 Upsert)
        # ==========================================
        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            # 加入時間戳，方便未來做 Data Lineage (數據血緣) 追蹤
            final_df['Extraction_Date'] = pd.to_datetime('today').normalize()

            loader.save_csv_backup(final_df)
            loader.upsert_to_db(final_df)

    except Exception as e:
        print(f"❌ ETL 管線發生致命錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())
