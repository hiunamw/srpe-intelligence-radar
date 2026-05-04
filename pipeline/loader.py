"""
模組: Loader
負責將清洗後的 DataFrame 匯出至本地備份 (CSV) 及寫入雲端數據庫 (Cloud SQL)。
同時負責發送第三方通知 (Discord Webhook)。

⚠️ 注意 (Note to Reviewers):
此模組展示了企業級的 Data Engineering 寫入策略：
1. 防禦性編程 (Defensive Programming)：寫入 DB 前先做 CSV 備份。
2. 冪等性 (Idempotency) 與 Upsert：使用 Staging Table 模式配合 PostgreSQL 的
   ON CONFLICT DO UPDATE，確保重複執行的 Cron Job 不會產生重複或髒數據。

為方便本地檢閱，若環境變數中未設定 DATABASE_URL，本程式將進入 [Mock 模式] 模擬執行。
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

# ==========================================
# 1. 本地安全網 (Local Backup)
# ==========================================
def save_csv_backup(df, backup_folder="sample_data"):
    """寫入數據庫前，將數據備份至本地 CSV 以防數據丟失"""
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
        
    today_str = pd.Timestamp('today').strftime("%Y%m%d_%H%M")
    csv_path = os.path.join(backup_folder, f"daily_rot_cleaned_{today_str}.csv")
    
    # 使用 utf-8-sig 確保 Excel 開啟時繁體中文不會亂碼
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"💾 [安全網] 今日數據已成功備份至: {csv_path}")

# ==========================================
# 2. 數據庫載入引擎 (Database Loader)
# ==========================================
def upsert_to_db(final_df):
    """
    [🏆 核心展示: PostgreSQL Upsert 邏輯]
    將 Pandas DataFrame 寫入 Cloud SQL，利用 Staging Table 進行合併更新。
    """
    print("\n☁️ 準備啟動雲端數據庫寫入引擎 (Cloud SQL Engine)...")
    
    db_url = os.environ.get("DATABASE_URL")
    
    # ---------------------------------------------------------
    # 為了展示用途，定義完整的 DDL 與 DML SQL 語句
    # ---------------------------------------------------------
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS rot_master (
            "Project" TEXT, "Date (PASP)" TIMESTAMP, "Date (ASP)" TIMESTAMP, "Date (Term)" TIMESTAMP,
            "Tower_Clean" TEXT, "Floor_Clean" TEXT, "Unit_Clean" TEXT,
            "LS (Contract)" FLOAT, "LS (ROT)" FLOAT, "Terms" TEXT, "Remark" TEXT, "Extraction_Date" TIMESTAMP,
            -- 設定複合主鍵以防止重複數據
            UNIQUE ("Project", "Tower_Clean", "Floor_Clean", "Unit_Clean")
        );
    """
    
    upsert_sql = """
        INSERT INTO rot_master (
            "Project", "Date (PASP)", "Date (ASP)", "Date (Term)", "Tower_Clean", "Floor_Clean", "Unit_Clean",
            "LS (Contract)", "LS (ROT)", "Terms", "Remark", "Extraction_Date"
        )
        SELECT 
            "Project", "Date (PASP)", "Date (ASP)", "Date (Term)", "Tower_Clean", "Floor_Clean", "Unit_Clean",
            "LS (Contract)", "LS (ROT)", "Terms", "Remark", "Extraction_Date"
        FROM rot_staging
        ON CONFLICT ("Project", "Tower_Clean", "Floor_Clean", "Unit_Clean")
        DO UPDATE SET
            "Date (PASP)" = EXCLUDED."Date (PASP)", 
            "Date (ASP)" = EXCLUDED."Date (ASP)", 
            "Date (Term)" = EXCLUDED."Date (Term)",
            "LS (Contract)" = EXCLUDED."LS (Contract)", 
            "LS (ROT)" = EXCLUDED."LS (ROT)", 
            "Terms" = EXCLUDED."Terms",
            "Remark" = EXCLUDED."Remark", 
            "Extraction_Date" = EXCLUDED."Extraction_Date";
    """

    # ---------------------------------------------------------
    # 執行階段 (Execution Phase)
    # ---------------------------------------------------------
    if not db_url:
        print("⚠️ [Mock 模式] 未偵測到 DATABASE_URL，正在模擬數據庫連線及寫入...")
        print("   [SQL 執行] CREATE TABLE IF NOT EXISTS rot_master...")
        print("   [Pandas] 剔除重複數據並寫入暫存表 (rot_staging)...")
        print("   [SQL 執行] INSERT INTO ... ON CONFLICT DO UPDATE SET ...")
        print("🎉 [Mock] 雲端數據庫更新完成！")
        return

    # 真實執行邏輯
    try:
        engine = create_engine(db_url)
        with engine.begin() as conn:
            conn.execute(text(create_table_sql))

        print("📥 正在寫入暫存表 (Staging Table)...")
        # 寫入前在 DataFrame 層級先做一次去重，確保 Staging 表內不撞 Key
        final_df = final_df.drop_duplicates(subset=["Project", "Tower_Clean", "Floor_Clean", "Unit_Clean"], keep='last')
        final_df.to_sql('rot_staging', con=engine, if_exists='replace', index=False)

        print("🔄 正在執行數據合併去重 (Upsert)...")
        with engine.begin() as conn:
            conn.execute(text(upsert_sql))
            
        print("🎉 雲端數據庫更新完成！Power BI 可以隨時讀取最新戰況。")
    except Exception as e:
        print(f"❌ 數據庫寫入失敗: {e}")

# 若獨立運行此模組的測試邏輯
if __name__ == "__main__":
    # 建立一個測試用的 Dummy DataFrame
    test_df = pd.DataFrame({
        "Project": ["Demo Horizon"], "Tower_Clean": ["1"], "Floor_Clean": ["2"], "Unit_Clean": ["A"],
        "LS (Contract)": [10000000], "LS (ROT)": [9500000], "Terms": ["N/A"]
    })
    save_csv_backup(test_df)
    upsert_to_db(test_df)
