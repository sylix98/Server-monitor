import psutil
import time
import smtplib
from datetime import datetime
from collections import deque 
from email.mime.text import MIMEText

# 確保上傳到VM執行能找到正確路徑
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import UserConfig 

# ================= 載入設定 =================
# Email
SMTP_SERVER = UserConfig.SMTP_SERVER
SMTP_PORT = UserConfig.SMTP_PORT
SENDER_EMAIL = UserConfig.SENDER_EMAIL
SENDER_PASSWORD = UserConfig.SENDER_PASSWORD
RECEIVER_EMAIL = UserConfig.RECEIVER_EMAIL

# 閾值與參數
CPU_THRESHOLD = UserConfig.CPU_THRESHOLD_PERCENT
NET_THRESHOLD = UserConfig.NET_THRESHOLD_PERCENT
MAX_BANDWIDTH = UserConfig.MAX_BANDWIDTH_BYTES_PER_SEC

CHECK_INTERVAL = UserConfig.CHECK_INTERVAL
COOLDOWN_SECONDS = UserConfig.ALERT_COOLDOWN_SECONDS
AVG_WINDOW = UserConfig.MOVING_AVERAGE_WINDOW

# 計算觸發次數 (Trigger Count)
CPU_TRIGGER_COUNT = (UserConfig.CPU_DURATION_MINUTES * 60) / CHECK_INTERVAL
NET_TRIGGER_COUNT = (UserConfig.NET_DURATION_MINUTES * 60) / CHECK_INTERVAL

# ================= 初始化變數 =================

# 計數器
cpu_high_counter = 0
net_high_counter = 0

# 冷卻計時器
last_cpu_alert_time = 0
last_net_alert_time = 0

# 3. 移動平均佇列 - 用來儲存最近 N 次的數據
cpu_history = deque(maxlen=AVG_WINDOW)
net_history = deque(maxlen=AVG_WINDOW)


# ================= 函式 =================

def send_alert_email(subject, body):
    """發送 Email"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f" -> [Email Sent] {subject}")
        return True
    except Exception as e:
        print(f" -> [Error] Email failed: {e}")
        return False

def get_network_speed():
    """計算當前的網路速度 (Bytes/sec)，會sleep秒"""
    old_val = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    time.sleep(1) 
    new_val = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    return new_val - old_val

def get_current_time():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")


# ================= 主程式 =================

print("=== Server Monitor Started (Optimized) ===")
print(f"Config: Check every {CHECK_INTERVAL}s | Avg Window: {AVG_WINDOW} samples | Cooldown: {COOLDOWN_SECONDS}s")
print(f"Target: CPU > {CPU_THRESHOLD}% ({UserConfig.CPU_DURATION_MINUTES}min) | Net > {NET_THRESHOLD}% ({UserConfig.NET_DURATION_MINUTES}min)")

try:
    while True:
        # 數據採集
        
        # 取得 CPU 單次數據
        raw_cpu = psutil.cpu_percent(interval=None)
        
        # 取得 網路 單次數據，耗時1秒
        raw_net_bytes = get_network_speed()
        raw_net_percent = (raw_net_bytes / MAX_BANDWIDTH) * 100

        # 數據平滑化      
        # 將新數據加入佇列
        cpu_history.append(raw_cpu)
        net_history.append(raw_net_percent)

        # 計算平均值 (用來判斷的數值)
        avg_cpu = sum(cpu_history) / len(cpu_history)
        avg_net = sum(net_history) / len(net_history)

        # 獲取當前時間
        current_time = get_current_time()
        
        # 判斷邏輯
        
        # 用平均值來判斷
        if avg_cpu > CPU_THRESHOLD:
            cpu_high_counter += 1
            print(f"[{current_time}] [CPU Warning] Avg: {avg_cpu:.1f}% (Raw: {raw_cpu}%) | Count: {cpu_high_counter}/{int(CPU_TRIGGER_COUNT)}")
        else:
            # 如果，計數器歸零
            if cpu_high_counter > 0:
                print(f"[{current_time}] [CPU Solved] Usage back to normal.")
            cpu_high_counter = 0

        # 觸發警報條件：計數達標 + 沒有在冷卻時間內
        if cpu_high_counter >= CPU_TRIGGER_COUNT:
            current_timestamp = time.time()
            
            # 檢查是否在冷卻時間內
            if (current_timestamp - last_cpu_alert_time) > COOLDOWN_SECONDS:
                success = send_alert_email(
                    f"[Alert] High CPU Load ({avg_cpu:.1f}%) on GCP Server",
                    f"CPU average usage has been over {CPU_THRESHOLD}% for {UserConfig.CPU_DURATION_MINUTES} minutes.\n"
                    f"Current Average: {avg_cpu:.1f}%\n"
                    f"Time: {current_time}"
                )
                if success:
                    last_cpu_alert_time = current_timestamp # 更新上次寄信時間
                    cpu_high_counter = 0 # 寄信後歸零重新計數
            else:
                print(f" -> [Suppress] CPU Alert ignored due to cooldown.")

        # 網路流量判斷邏輯
        
        if avg_net > NET_THRESHOLD:
            net_high_counter += 1
            mb_speed = raw_net_bytes / 1024 / 1024
            print(f"[{current_time}] [Net Warning] Avg: {avg_net:.1f}% (Speed: {mb_speed:.2f} MB/s) | Count: {net_high_counter}/{int(NET_TRIGGER_COUNT)}")
        else:
            if net_high_counter > 0:
                print(f"[{current_time}] [Net Solved] Traffic back to normal.")
            net_high_counter = 0

        if net_high_counter >= NET_TRIGGER_COUNT:
            current_timestamp = time.time()
            
            if (current_timestamp - last_net_alert_time) > COOLDOWN_SECONDS:
                success = send_alert_email(
                    f"[Alert] High Network Traffic ({avg_net:.1f}%)",
                    f"Network average usage has been over {NET_THRESHOLD}% for {UserConfig.NET_DURATION_MINUTES} minutes.\n"
                    f"Current Average Level: {avg_net:.1f}%\n"
                    f"Time: {current_time}"
                )
                if success:
                    last_net_alert_time = current_timestamp
                    net_high_counter = 0
            else:
                print(f" -> [Suppress] Net Alert ignored due to cooldown.")

        # 補眠 (扣掉 get_network_speed 的 1 秒)
        time.sleep(max(0, CHECK_INTERVAL - 1))

except KeyboardInterrupt:
    print("\nMonitor stopped by user.")