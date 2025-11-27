# ================= Email 設定 =================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = ""
SENDER_PASSWORD = "" 
RECEIVER_EMAIL = ""

# ================= 監控閥值與時間設定 =================

# CPU
CPU_THRESHOLD_PERCENT = 80      # Free Tier 的 VM 設 80%
CPU_DURATION_MINUTES = 2        # 持續 N 分鐘才視為異常

# 網路
NET_THRESHOLD_PERCENT = 90      # 流量使用率超過 N%
NET_DURATION_MINUTES = 1        # 持續 N 分鐘才視為異常
# 頻寬上限 (Bytes/sec) - 5MB/s (5,000,000)  暫不確定GCP免費版VM能接受的最大流量為多少
MAX_BANDWIDTH_BYTES_PER_SEC = 5000000 

# ================= 進階設定 =================

# 檢查頻率 (秒)
CHECK_INTERVAL = 10 

# 警報冷卻時間 (秒)
# 發送一次警報後，接下來 60 秒內就算異常也不會再寄信 (避免信箱被訊息灌爛)
ALERT_COOLDOWN_SECONDS = 600 

# 數據平滑化視窗 (次數)
# 不看單次數值，而是看最近 N 次的平均值 (過濾瞬間大量的數值)
# 取最近 3 次 (約30秒) 的平均來判斷是否超過閥值
MOVING_AVERAGE_WINDOW = 3

