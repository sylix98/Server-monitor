# GCP Server Health Monitor & Alert System (GCP 伺服器健康度監控與自動警報系統)

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-GCP_Compute_Engine-orange?logo=google-cloud)
![OS](https://img.shields.io/badge/OS-Linux_Ubuntu-yellow?logo=linux)
![License](https://img.shields.io/badge/License-MIT-green)

## 專案簡介

這是一個部署於 **Google Cloud Platform (GCP)** 的輕量級伺服器監控解決方案。
專案旨在解決雲端虛擬機 (VM) 在資源受限環境下（如 Free Tier），難以即時掌握資源異常的問題。系統透過 Python 腳本持續監測 **CPU 使用率**與**網路流量**，並結合 **Systemd** 實現高可用性的背景服務管理。

與一般監控腳本不同，本系統引入了 **「移動平均 (Moving Average)」** 與 **「時間窗口 (Time Window)」** 演算法，有效過濾瞬間突波 (Spike) 造成的誤報，並具備 **警報冷卻 (Cooldown)** 機制，是具備維運思維的自動化工具。

注意：本專案僅用在個人程式與雲端練習面向，不得用於其他用途。

## 核心功能

* **雲端原生部署**：實作於 GCP Compute Engine (Linux/Ubuntu)。
* **智慧型監控邏輯**：
    * **防誤報機制**：非單點觸發，需連續 N 分鐘超過閾值才視為異常（CPU 預設 3 分鐘 / 網路 1 分鐘）。
    * **數據平滑化**：採用移動平均法 (Moving Average) 消除雜訊。
* **自動化警報通知**：整合 SMTP 服務 (Gmail)，當系統負載異常時，自動發送包含詳細數據與時間戳記的 Email。
* **Systemd 服務管理**：將程式註冊為 Linux 系統服務，支援開機自啟 (Auto-start) 與崩潰自動重啟 (Auto-restart)。
* **警報冷卻機制**：避免在持續異常狀態下重複發送垃圾郵件，提升維運體驗。

## 使用技術

* **語言**：Python 3 (使用 `psutil` 進行系統資源採集, `smtplib` 處理郵件發送)
* **作業系統**：Linux (Ubuntu 22.04 LTS)
* **雲端平台**：Google Cloud Platform (GCP)
* **自動化與維運**：Systemd (Service Management), Bash Script, SSH
* **版本控制**：Git

## 安裝與部署

### 1. 環境準備
確保已安裝 Python 3 及 `pip`。

```bash
sudo apt update
sudo apt install python3-pip python3-venv -y
```

### 2. 專案克隆 
```git clone [https://github.com/你的帳號/你的專案名稱.git](https://github.com/你的帳號/你的專案名稱.git)
cd 你的專案名稱
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### 3. 設定參數 (UserConfig.py)
修改設定檔以符合您的環境需求：

**UserConfig.py**
```
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # Google 應用程式密碼
```

**監控閾值設定**
```
CPU_THRESHOLD_PERCENT = 70
CPU_DURATION_MINUTES = 3
MAX_BANDWIDTH_BYTES_PER_SEC = 5000000 # 5MB/s
```
### 4. 設定 Systemd 服務 (Daemonize)
為了讓程式在背景持續運行，需建立 Systemd 服務檔案：

**Bash**
```
sudo nano /etc/systemd/system/server-monitor.service
```

**內容範例：**
```
[Unit]
Description=GCP Server Health Monitor Service
After=network.target

[Service]
Type=simple
User=你的使用者名稱
WorkingDirectory=/home/你的使用者名稱/server-monitor
ExecStart=/home/你的使用者名稱/server-monitor/venv/bin/python3 monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

**啟動服務**

**Bash**
```
sudo systemctl daemon-reload
sudo systemctl start server-monitor
sudo systemctl enable server-monitor
```

## 成果
