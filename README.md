# 📡 SRPE Daily Intelligence Radar (一手住宅物業銷售資訊雷達)

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Playwright](https://img.shields.io/badge/playwright-async-green)
![Data Extraction](https://img.shields.io/badge/pdfplumber-hybrid_strategy-orange)
![Data Pipeline](https://img.shields.io/badge/ETL-Daily_Automated-red)

An automated End-to-End data pipeline that monitors, scrapes, and parses the Sales of First-hand Residential Properties Electronic Platform (SRPE) in Hong Kong, delivering real-time Discord alerts and structured Excel reports daily.

## 📖 項目簡介 (Project Overview)
本項目旨在自動化追蹤香港一手住宅物業市場的最新動態，為定價團隊及管理層提供極速的市場情報。系統採用 Mono-Repo 設計，每日自動處理繁瑣的政府 PDF 文件。

## ✨ 核心模組 (Core Modules)

**1. 🔔 每日情報通知雷達 (`main_radar.py`)**
* **實時監控**：每日掃描 SRPE 網站，追蹤 24 小時內更新的四大類文件 (SB, PL, SA, ROT)。
* **Discord 智能推送**：自動排版並透過 Webhook 將摘要推送到群組，內置分段發送器完美繞過 2000 字元限制。

**2. 🧹 每日成交數據處理器 (`main_etl.py`)**
* **自動化下載 (Extract)**：利用 `playwright` 模擬無頭瀏覽器，自動處理並繞過政府網站免責聲明獲取 Token，批量下載目標樓盤的成交紀錄冊 PDF。
* **高階數據清洗 (Transform)**：
  * 深度定制 `pdfplumber`，獨創「混合雙打抽取法 (Hybrid Strategy)」解決表格漏畫底線問題。
  * 構建強大的 Regex 引擎，精準拆解「子母座」、智能縮寫「洋房/別墅」，並強行攔截「特色戶 (Simplex/Duplex)」等極端排版。
* **自動化報表 (Load)**：一鍵將雜亂無章的 PDF 轉換為高管級別、自動調整欄寬的 Excel `ROTs_{yesterday}.xlsx`。

## 📝 系統架構 (Architecture Diagram)
![系統架構圖](assets/architecture_diagram.svg)

## 📊 輸出展示 (Sample Outputs)

本系統每日會自動生成兩種維度的情報輸出，兼顧「即時性」與「分析深度」：

### 1. Discord 實時情報推送 (Real-time Alert)
自動對長篇幅的銷售安排與樓盤異動進行格式化，並推送到 Discord 群組。
![Discord 實時推送預覽](assets/discord_demo.png)

### 2. 結構化成交數據庫 (Cleaned ROT Excel)
從雜亂無章的 PDF 提取並清洗出成交數據，將特例排版（如子母座、特色戶 Simplex/Duplex 等）標準化，並輸出至 Excel。

PDF 原圖 (1): The Aperture
![PDF 原圖預覽 (1)](assets/rot_demo_pdf_1.png)

PDF 原圖 (2): Southland
![PDF 原圖預覽 (2)](assets/rot_demo_pdf_2.png)

清洗前
![Excel 數據清洗結果預覽 (Before)](assets/rot_demo_before.png)

清洗後
![Excel 數據清洗結果預覽 (After)](assets/rot_demo_after.png)

## 🛠️ 技術棧 (Tech Stack)
* **Language:** Python
* **Web Scraping:** `playwright`, `requests`, `asyncio`
* **Data Engineering:** `pandas`, `pdfplumber`, `re` (Regular Expressions)
* **Output & Notification:** `xlsxwriter`, Discord Webhooks

## 🚀 關於源代碼 (About Source Code)
> **⚠️ 櫥窗展示聲明 (Showcase Notice)**
> 為保護商業價值及防止濫用，本 Repository 內的 `main_radar.py` 及 `main_etl.py` 為展示系統架構與代碼風格的閹割版 (Teaser Version)。核心的反爬蟲繞過機制及 PDF 清洗 Regex 已被隱藏。
> **歡迎在面試中進一步探討完整的技術細節與數據工程思維。**

### 環境設定 (Configuration)
```bash
pip install requests playwright pdfplumber nest_asyncio pandas xlsxwriter
playwright install chromium
```

## 🗺️ 未來規劃 (Roadmap)
- [ ] **支付條款 (Terms) 深度解析 (NLP / Text Mining)**：

  目前系統完整保留了 ROT 的支付條款長文。下一步計劃引入 NLP 或 LLM 技術，從繁雜的條款中萃取出核心特徵，例如「折扣率 (Discount Rate)」、「提早成交回贈 (Cash Rebate)」及「付款期 (Payment Period)」，以計算最真實的折實價 (Net Price)。
- [ ] **車位 (CP) 結構化分離**：

  升級清洗引擎，以正則表達式精準提取車位號碼及數量，並轉換為獨立的數據維度 (`Has_CP`, `CP_Count`)，以提升平均呎價計算的準確度。
- [ ] **數據庫整合與自動化 BI**：

  將每日洗淨的 DataFrame 匯入 PostgreSQL，建立歷史數據倉儲 (Data Warehouse)，並直接串接 PowerBI / Tableau 進行實時可視化。
