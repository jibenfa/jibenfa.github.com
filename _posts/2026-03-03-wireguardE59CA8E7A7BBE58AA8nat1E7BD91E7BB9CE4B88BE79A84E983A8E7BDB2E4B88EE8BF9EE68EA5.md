---
id: 828
title: wireguard在移动nat1网络下的部署与连接
date: 2026-03-03 00:13:13+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- python
- wireguard
- lucky
- stun
- cloudflare
- ddns
- natmap
---

最近碰到这么两个场景，网络环境是中国移动家庭宽带，分配的是动态ipv6公网地址和ipv4内网地址（nat1），光猫拨号，openwrt路由位于光猫之后，想通过wireguard连回家（使用windows客户端）。

场景一：wireguard直连openwrt的ipv6地址即可，这里就不多说了，毫无压力。当然需要把光猫上的v6的防火墙关闭。

场景二：光猫上居然没有ipv6的防火墙选项，而且ipv6的入站连接除了ICMP包外都是阻断的，折腾很久都没成功。研究了一下，最后采用了如下办法成功实现了wireguard连回家：

1.在openwrt上部署lucky（2026-03-23改为natmap），并用lucky的stun内网穿透功能获取外网ipv4地址和端口；

2.通过lucky的webhook（2026-03-23改为sh脚本）把ip和端口更新到cloudflare下托管域名的TXT记录（哪里都有cloudflare大善人的身影）；

3.windows客户端运行python脚本（打包成exe直接执行）通过域名DNS查询TXT记录，并替换wireguard配置文件中的endpoint的ip和端口，然后发起连接，并轮询相关TXT记录，发生变化时重新连接。

详细步骤如下：

1.下载安装lucky：

从<a href="https://github.com/gdy666/luci-app-lucky">这个页面</a>的release下下载3个文件（我的是x86的openwrt）：
```
lucky_2.19.4_Openwrt_x86_64.ipk
luci-app-lucky_2.2.2-r1_all.ipk
luci-i18n-lucky-zh-cn_25.051.13443.e78d498_all.ipk
```
上传到openwrt路由上的/tmp，然后安装
```bash
cd /tmp
opkg update
opkg install jq
opkg install lucky_2.19.4_Openwrt_x86_64.ipk
opkg install luci-app-lucky_2.2.2-r1_all.ipk
opkg install luci-i18n-lucky-zh-cn_25.051.13443.e78d498_all.ipk
```
2.配置lucky，打开lucky页面，设置好路径、密码后，打开“stun内网穿透”菜单，点击设置，先更新一波stun服务器列表，然后点击“添加穿透规则”，按图设置：

<img src="https://jibenfa.github.io/uploads/2026/03/lucky_mainset.png" width="1390" height="398" alt="lucky的主要设置" />

其中172.24.1.1是部署wireguard的网关局域网ip。

设置完先保存一下，看看是否能正常获取到ip和端口：

<img src="https://jibenfa.github.io/uploads/2026/03/lucky_ip_port.png" width="1390" height="398" alt="lucky获取ip和端口" />

3.登录cloudflare，在域名的dns下，新建一个TXT记录，例如：wg.xxx.com的TXT记录，内容随便写，如图所示。

<img src="https://jibenfa.github.io/uploads/2026/03/cf_dns_txt.png" width="1390" height="398" alt="cloudflare的TXT记录" />

4.创建token，如图所示，生成一个“编辑区域 DNS”的令牌，注意要把token复制下来。

<img src="https://jibenfa.github.io/uploads/2026/03/cf_token.png" width="1390" height="398" alt="cloudflare下创建token" />

然后运行以下脚本：
```bash
#!/bin/sh
#opkg update
#opkg install jq

CF_TOKEN="YOUR_TOKEN"   #上一步里面拿到的token
ZONE="xxx.com"   #你的主域名
NAME="wg.xxx.com"  #TXT记录的子域名
CONTENT="ip:port"

# 1️⃣ 获取 ZONE_ID
ZONE_ID=$(curl -s -X GET \
"https://api.cloudflare.com/client/v4/zones?name=$ZONE" \
-H "Authorization: Bearer $CF_TOKEN" \
-H "Content-Type: application/json" \
| jq -r '.result[0].id')

# 2️⃣ 获取已有 TXT RECORD_ID
RECORD_ID=$(curl -s -X GET \
"https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=TXT&name=$NAME" \
-H "Authorization: Bearer $CF_TOKEN" \
| jq -r '.result[0].id')

# 3️⃣ 更新（不会新增）
curl -s -X PUT \
"https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
-H "Authorization: Bearer $CF_TOKEN" \
-H "Content-Type: application/json" \
--data "{
  \"type\":\"TXT\",
  \"name\":\"$NAME\",
  \"content\":\"$CONTENT\",
  \"ttl\":60
}"

echo ""

echo "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID"
echo "Authorization: Bearer $CF_TOKEN"
```

运行后如果结果含有"success":true 字样表示成功了，如图所示：

<img src="https://jibenfa.github.io/uploads/2026/03/cf_script_success.png" width="1390" height="398" alt="脚本执行成功" />


复制上图最后两行内容，等会儿有用，最后两行内容看起来像：
```
https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID
Authorization: Bearer $CF_TOKEN"
```

5.打开lucky页面，打开“stun内网穿透”菜单，找到之前那条规则，点击编辑图标，按照下图填写：
<img src="https://jibenfa.github.io/uploads/2026/03/lucky_webhook.png" width="1390" height="398" alt="lucky的webhook设置" />

其中：

1）“接口地址”填写上一步中复制的网址，形如如下的字符串（$变量替换为真实的值）：
```
https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID
```
2）"请求方法"选择“put”

3）“请求头”填写上一步中复制的token，形如如下的字符串（$变量替换为真实的值）：
```
Authorization: Bearer $CF_TOKEN"
```
4）“请求体”填写：
```json
{
    "type":"TXT",
    "name":"wg",
    "content":"#{ipAddr}",
    "ttl":60
}
```
其中的#{ipAddr}会由lucky在运行时自动替换成获取到的ip和端口。

5）“接口调用成功包含的字符串”填写："success":true

最后点击修改后退出，等一会儿后，如果webhook运行成功，会如下图提示：

<img src="https://jibenfa.github.io/uploads/2026/03/lucky_webhook_success.png" width="1390" height="398" alt="lucky的webhook执行成功" />

6.使用如下python脚本wg.py打包生成一个wireguard客户端，搭配config.ini配置文件和原版wireguard的windows客户端使用。exe文件需要和config.ini文件放到同一个目录下。

config.ini文件如下：其中wg1.conf就是windows下wireguard客户端使用的配置文件，里面的endpoint会自动由wg.py替换成真实的ip和端口，其他配置可按真实情况填写：
```
[wireguard]
wireguard_exe = C:\Program Files\WireGuard\wireguard.exe
conf_file = D:\wg\wg1.conf
check_ip = 172.24.1.1

[dns]
txt_domain = wg.xxx.com
dns_server = 223.5.5.5,172.24.1.1
lifetime = 15

[check]
interval = 5
ping_timeout_ms = 1000

```

wg.py是一个带界面的客户端：
```python
import subprocess
import time
import dns.resolver
import re
import os
import psutil
import configparser
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageDraw, ImageFont
import pystray

# ==========================
# 配置读取
# ==========================
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

WIREGUARD_EXE = config["wireguard"]["wireguard_exe"]
CONF_FILE = config["wireguard"]["conf_file"]
CHECK_IP = config["wireguard"]["check_ip"]

TXT_DOMAIN = config["dns"]["txt_domain"]
DNS_SERVERS = [x.strip() for x in config["dns"]["dns_server"].split(",") if x.strip()]
DNS_LIFETIME = int(config["dns"]["lifetime"])

CHECK_INTERVAL = int(config["check"]["interval"])
PING_TIMEOUT = config["check"]["ping_timeout_ms"]

ENDPOINT_PATTERN = r"(\d{1,3}(?:\.\d{1,3}){3}:\d+)"

resolver = dns.resolver.Resolver()
resolver.nameservers = DNS_SERVERS
resolver.lifetime = DNS_LIFETIME

last_endpoint = None
loop_running = False
loop_thread = None
tray_icon = None

# ==========================
# GUI 日志输出
# ==========================
def log(msg):
    timestamp = time.strftime("%H:%M:%S")
    text_area.configure(state="normal")
    text_area.insert(tk.END, f"[{timestamp}] {msg}\n")
    text_area.see(tk.END)
    text_area.configure(state="disabled")
    print(msg)

# ==========================
# WireGuard 功能
# ==========================
def get_endpoint_from_txt():
    try:
        answers = resolver.resolve(TXT_DOMAIN, "TXT", tcp=True)
        for r in answers:
            if hasattr(r, "strings"):
                txt = "".join([s.decode(errors="ignore") for s in r.strings])
            else:
                txt = r.to_text().strip('"')
            match = re.search(ENDPOINT_PATTERN, txt)
            if match:
                return match.group(1)
    except Exception as e:
        log(f"TXT query failed: {e}")
    return None

def update_conf_endpoint(new_endpoint):
    lines = []
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().lower().startswith("endpoint"):
                lines.append(f"Endpoint = {new_endpoint}\n")
            else:
                lines.append(line)
    with open(CONF_FILE, "w", encoding="utf-8") as f:
        f.writelines(lines)

def run_wg(args):
    result = subprocess.run(
        [WIREGUARD_EXE] + args,
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW  # ✅ 防止弹出窗口
    )
    if result.returncode != 0:
        log(result.stderr.decode(errors="ignore"))
    return result

def uninstall_tunnel():
    killed = 0
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == "wireguard.exe":
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    log(f"{killed} WireGuard process(es) terminated.")

def install_tunnel():
    log("Installing tunnelservice...")
    run_wg(["/installtunnelservice", CONF_FILE])

def is_tunnel_up():
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(PING_TIMEOUT), CHECK_IP],
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW  # ✅ 防止闪现窗口
        )
        return b"TTL=" in result.stdout
    except Exception as e:
        log(f"Ping check failed: {e}")
        return False

def ensure_tunnel(new_endpoint):
    log(f"Updating tunnel -> {new_endpoint}")
    uninstall_tunnel()
    update_conf_endpoint(new_endpoint)
    install_tunnel()
    log("Tunnel updated")

# ==========================
# 主循环
# ==========================
def wg_loop():
    global last_endpoint, loop_running
    status_label.config(text="已连接")
    while loop_running:
        endpoint = get_endpoint_from_txt()
        if endpoint and endpoint != last_endpoint:
            log(f"New endpoint detected: {endpoint}")
            ensure_tunnel(endpoint)
            last_endpoint = endpoint
        elif endpoint and not is_tunnel_up():
            log("Tunnel down, restarting")
            ensure_tunnel(endpoint)
        time.sleep(CHECK_INTERVAL)
    uninstall_tunnel()
    status_label.config(text="未连接")
    log("Tunnel stopped")
    toggle_button.config(state="normal", text="启动")

# ==========================
# GUI 控制
# ==========================
def start_stop_loop():
    global loop_running, loop_thread
    if not loop_running:
        loop_running = True
        loop_thread = threading.Thread(target=wg_loop, daemon=True)
        loop_thread.start()
        toggle_button.config(text="停止")
    else:
        toggle_button.config(state="disabled")
        loop_running = False

# ==========================
# 托盘支持
# ==========================
def make_icon():
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # 透明背景
    draw = ImageDraw.Draw(image)

    # 画圆形背景
    draw.ellipse((0, 0, size-1, size-1), fill=(0, 120, 215, 255))  # Windows 蓝

    # 画字母 "WG"
    try:
        font = ImageFont.truetype("seguiemj.ttf", 28)  # 系统字体
    except:
        font = ImageFont.load_default()

    text = "WG"
    bbox = draw.textbbox((0, 0), text, font=font)  # 获取文字边界
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    draw.text(((size - w) / 2, (size - h) / 2), text, font=font, fill="white")

    return image

def create_tray_icon_once():
    global tray_icon
    if tray_icon is None:
    
        def on_show(icon, item):
            icon.stop()
            root.after(0, root.deiconify)

        def on_quit(icon, item):
            icon.stop()
            global loop_running
            loop_running = False
            uninstall_tunnel()
            root.after(0, root.destroy)

        def on_toggle(icon, item):
            root.after(0, start_stop_loop)

        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", on_show),
            pystray.MenuItem("启动/停止 WireGuard", on_toggle),
            pystray.MenuItem("退出", on_quit)
        )
        tray_icon = pystray.Icon("wg_updater", make_icon(), "WireGuard Updater", menu)
        threading.Thread(target=tray_icon.run, daemon=True).start()

def minimize_to_tray():
    root.withdraw()  # 隐藏窗口，任务栏不显示
    create_tray_icon_once()

# ==========================
# GUI 布局
# ==========================
root = tk.Tk()
root.title("WireGuard under STUN Peer Using DNS TXT Updater")
root.geometry("800x600")

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 16, "bold"), padding=10)
style.configure("TLabel", font=("Segoe UI", 14, "bold"))

toggle_button = ttk.Button(root, text="启动", command=start_stop_loop)
toggle_button.pack(pady=15)

status_label = ttk.Label(root, text="未连接")
status_label.pack(pady=10)

text_area = scrolledtext.ScrolledText(root, width=100, height=25, state="disabled", font=("Consolas", 11))
text_area.pack(padx=10, pady=10, fill="both", expand=True)

# 自动最小化到托盘
def on_minimize(event):
    minimize_to_tray()
root.bind("<Unmap>", on_minimize)

root.mainloop()
```

使用界面如下：
<img src="https://jibenfa.github.io/uploads/2026/03/wg_updater_1.png" width="1390" height="398" alt="客户端初始界面" />

<img src="https://jibenfa.github.io/uploads/2026/03/wg_updater_2.png" width="1390" height="398" alt="客户端运行界面" />

<img src="https://jibenfa.github.io/uploads/2026/03/wg_updater_3.png" width="1390" height="398" alt="客户端停止界面" />

----------------------------------------------------------------------------------------------------------------------
2026-03-22 更新：
使用过程中发现lucky内置的端口转发似乎不太稳定，于是，弃用lucky，改用natmap，并使用opewnrt自带的端口转发。如图：
1.安装和配置natmap

```bash
opkg update
opkg install natmap luci-app-natmap
vi /etc/config/natmap
```
配置文件内容为：

```vim
config natmap
        option enable '1'
        option udp_mode '1'
        list stun_server 'stun.l.google.com:19302'
        list stun_server 'stun1.l.google.com:19302'
        list stun_server 'stun2.l.google.com:19302'
        list stun_server 'stun.cloudflare.com:3478'
        option http_server 'baidu.com'
        option port '5582'
        option log_stdout '1'
        option log_stderr '1'
        option interface 'wan'
        option interval '1'
        option stun_cycle '60'
        option forward_target '172.24.1.1'
        option forward_port '53820'
        option family 'ipv4'
        option notify_script '/root/natmap_txt.sh'
```

然后创建/root/natmap_txt.sh:

```bash
touch /root/natmap_txt.sh
chmod +x /root/natmap_txt.sh
vi /root/natmap_txt.sh
```

natmap_txt.sh内容为（ZONE_ID，RECORD_ID，CF_TOKEN替换为真实的值）：

```vim
#!/bin/sh

# 找 natmap json
for f in /var/run/natmap/*.json; do
    IP=$(jsonfilter -i "$f" -e '@.ip' 2>/dev/null)
    [ -n "$IP" ] && NATMAP_JSON="$f" && break
done

[ -z "$NATMAP_JSON" ] && exit 1

PORT=$(jsonfilter -i "$NATMAP_JSON" -e '@.port')

TXT="${IP}:${PORT}"

echo "NATMAP → $TXT"

curl -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -H "Content-Type: application/json" \
  --data @- <<EOF
{
  "type": "TXT",
  "name": "wg",
  "content": "$TXT",
  "ttl": 60
}
EOF
```

2.使用openwrt自带的端口转发
<img src="https://jibenfa.github.io/uploads/2026/03/luci_firewall_port_forward.png" width="1390" height="398" alt="打开openwrt端口映射" />


参考：

1.chatgpt