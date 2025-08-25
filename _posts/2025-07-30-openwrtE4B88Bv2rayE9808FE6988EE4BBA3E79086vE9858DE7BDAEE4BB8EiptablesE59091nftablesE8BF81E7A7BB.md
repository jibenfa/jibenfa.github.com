---
id: 821
title: openwrt下v2ray透明代理配置从iptables向nftables迁移
date: 2025-07-30 03:22:13+00:00
author: coffeecat
layout: post
categories:
- openwrt
- 科学上网
tags:
- openwrt
- 科学上网
---

由于openwrt的防火墙逐步从iptables向nftables升级，官方24.10.2的dnsmasq包默认不将ipset纳入编译选项，只支持nftset，
由此带来v2ray透明代理的配置必须进行升级，此次主要是调整了v2ray的配置和dnsmasq-full的配置。

1）修改/etc/init.d/v2ray

 ```bash

  
#!/bin/sh /etc/rc.common
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.
#
# To use this file, install chinadns,v2ray,dnsmasq-full,bind-dig,coreutils-nohup,coreutils-paste first
#
#!/bin/sh /etc/rc.common

START=90
USE_PROCD=1

DOMAIN="xxx.com" #需改为实际网址。同时在dnsmasq配置文件中设置nftset=/xxx.com/114.114.114.114
DNS_SERVER="114.114.114.114"
BACKUP_DNS_SERVER="119.29.29.29 223.5.5.5 180.76.76.76"
LOCAL_IP="127.0.0.1"
#CHINADNS和V2RAY端口范围:5354-5355 5356-5357 5358-5359 5360-5361，须搭配对应的chinadns和v2ray配置文件使用
CHINADNS_MIN_PORT="5354"
CHNROUTE_FILE="/etc/chinadns_chnroute.txt"
V2RAY_PORT="1060"
V2RAY_MAX_DNS_PORT="5361"
V2RAY_DNS_PORTS="5357 5359 5361"
V2RAY_BIN="/usr/bin/v2ray"
V2RAY_CONF="/etc/config/v2ray.json"

set_multi_domestic_dns() {
    current_dns_list=`uci get dhcp.@dnsmasq[0].server 2>/dev/null`
    if [ x${DNS_SERVER:0:15} != x${current_dns_list:0:15} ]; then
        echo "[+] 设置使用国内DNS服务器"
        uci -q delete dhcp.@dnsmasq[0].server
        uci add_list dhcp.@dnsmasq[0].server=${DNS_SERVER}
        for dns in $BACKUP_DNS_SERVER; do
            uci add_list dhcp.@dnsmasq[0].server="${dns}"
        done
        uci set dhcp.@dnsmasq[0].noresolv=0
        uci set dhcp.@dnsmasq[0].nohosts=0
        uci commit dhcp
        echo "[+] 重启dnsmasq服务"
        /etc/init.d/dnsmasq restart 1>/dev/null 2>&1
        echo "[✓] 完成"
    fi
}

set_multi_foreign_dns() {
    current_dns_list=`uci get dhcp.@dnsmasq[0].server 2>/dev/null`
    if [ x${LOCAL_IP:0:9} != x${current_dns_list:0:9} ]; then
        echo "[+] 设置使用ChinaDNS DNS服务器"
        chinadns_port=`uci get chinadns.@chinadns[0].port 2>/dev/null`
        chinadns_listen_ipport=${LOCAL_IP}"#"${chinadns_port}
        uci -q delete dhcp.@dnsmasq[0].server
        uci add_list dhcp.@dnsmasq[0].server=${chinadns_listen_ipport}
        for port in $V2RAY_DNS_PORTS; do
            uci add_list dhcp.@dnsmasq[0].server="${LOCAL_IP}#${port}"
        done
        uci set dhcp.@dnsmasq[0].noresolv=1
        uci set dhcp.@dnsmasq[0].nohosts=1
        uci commit dhcp
        echo "[+] 重启dnsmasq服务"
        /etc/init.d/dnsmasq restart 1>/dev/null 2>&1
        echo "[✓] 完成"
    fi
}

create_bypasslist() {
    echo "[*] 创建 inet v2ray 表和 bypasslist 集合"

    # 创建 table（如不存在）
    nft list table inet v2ray 2>/dev/null >/dev/null
    if [ $? -ne 0 ]; then
        nft add table inet v2ray
    fi

    # 创建或清空 set：bypasslist
    if nft list set inet v2ray bypasslist 2>/dev/null >/dev/null; then
        nft delete set inet v2ray bypasslist
    fi

    # 创建 bypasslist 集合
    nft add set inet v2ray bypasslist { type ipv4_addr\; flags interval\;}

    # 添加私有地址段
    echo "[+] 添加内网地址段到 bypasslist"
    nft add element inet v2ray bypasslist { \
        0.0.0.0/8, 10.0.0.0/8, 127.0.0.0/8, \
        169.254.0.0/16, 172.16.0.0/12, \
        192.168.0.0/16, 224.0.0.0/4, 240.0.0.0/4 \
    }

    # 加载国内 IP（来自文件）
    if [ -f "$CHNROUTE_FILE" ]; then
        echo "[+] 加载国内 IP 到 bypasslist（来源: $CHNROUTE_FILE）"
        BATCH_SIZE=1000
        count=0
        batch=""

        echo "[*] 正在批量导入到 nftables..."

        while read -r line; do
            [ -z "$line" ] && continue
            [ "${line#\#}" != "$line" ] && continue

            batch="$batch $line,"
            count=$((count + 1))

            if [ "$count" -ge "$BATCH_SIZE" ]; then
                batch="${batch%,}"
                nft add element inet v2ray bypasslist { $batch }
                count=0
                batch=""
            fi
        done < "$CHNROUTE_FILE"

        if [ -n "$batch" ]; then
            batch="${batch%,}"
            nft add element inet v2ray bypasslist { $batch }
        fi

        echo "[✓] 导入完成"
    else
        echo "[!] 未找到国内 IP 文件: $CHNROUTE_FILE"
    fi

    # 加载 VPS 域名解析结果
    echo "[+] 解析 $DOMAIN 并加入 bypasslist"
    for ip in $(dig +short "$DOMAIN" @"$DNS_SERVER" | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}'); do
        nft add element inet v2ray bypasslist { $ip }
        echo "    加入 $ip"
    done
    echo "    bypasslist 已载入 $(nft list set inet v2ray bypasslist | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(/[0-9]+)?' | wc -l) 条目"

    # 创建 nat 类型链
    nft list chain inet v2ray prerouting 1>/dev/null 2>&1 || nft add chain inet v2ray prerouting { type nat hook prerouting priority dstnat\; }
    nft list chain inet v2ray output 1>/dev/null 2>&1 || nft add chain inet v2ray output { type nat hook output priority -100\; }
}

create_gfwlist(){
    echo "[*] 创建 inet v2ray 表和 gfwlist 集合"

    # 创建 table（如不存在）
    nft list table inet v2ray 2>/dev/null >/dev/null
    if [ $? -ne 0 ]; then
        nft add table inet v2ray
    fi

    # 创建或清空 set：gfwlist
    if nft list set inet v2ray gfwlist 2>/dev/null >/dev/null; then
        nft delete set inet v2ray gfwlist
    fi

    # 创建 gfwlist 集合
    nft add set inet v2ray gfwlist { type ipv4_addr\;}

    # 注意dnsmasq配置文件中也有gfwlist的内容，所以需要重新加载,此操作不会直接增加gfwlist条目数，只会在解析网址时动态增加
    /etc/init.d/dnsmasq reload 1>/dev/null 2>&1
    echo "    gfwlist 已载入 $(nft list set inet v2ray gfwlist | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(/[0-9]+)?' | wc -l) 条目"

    # 创建 nat 类型链
    nft list chain inet v2ray prerouting 1>/dev/null 2>&1 || nft add chain inet v2ray prerouting { type nat hook prerouting priority dstnat\; }
    nft list chain inet v2ray output 1>/dev/null 2>&1 || nft add chain inet v2ray output { type nat hook output priority -100\; }
}

enable_bypasslist_firewall_rules(){
    nft add rule inet v2ray prerouting ip daddr != @bypasslist tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet v2ray output ip daddr != @bypasslist tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet v2ray prerouting ip daddr ${LOCAL_IP} udp dport ${CHINADNS_MIN_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet v2ray output ip daddr ${LOCAL_IP} udp dport ${CHINADNS_MIN_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet v2ray prerouting ip daddr != @bypasslist udp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet v2ray output ip daddr != @bypasslist udp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
}

disable_bypasslist_firewall_rules(){
    nft delete rule inet v2ray prerouting ip daddr != @bypasslist tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft delete rule inet v2ray output ip daddr != @bypasslist tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft delete rule inet v2ray prerouting ip daddr ${LOCAL_IP} udp dport ${CHINADNS_MIN_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft delete rule inet v2ray output ip daddr ${LOCAL_IP} udp dport ${CHINADNS_MIN_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft delete rule inet v2ray prerouting ip daddr != @bypasslist udp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft delete rule inet v2ray output ip daddr != @bypasslist udp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
}

enable_gfwlist_firewall_rules(){
    nft add rule inet v2ray prerouting ip daddr @gfwlist tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet v2ray output ip daddr @gfwlist tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet v2ray prerouting ip daddr ${LOCAL_IP} udp dport ${CHINADNS_MIN_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet v2ray output ip daddr ${LOCAL_IP} udp dport ${CHINADNS_MIN_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet v2ray prerouting ip daddr @gfwlist udp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet v2ray output ip daddr @gfwlist udp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
}

disable_gfwlist_firewall_rules(){
    nft delete rule inet v2ray prerouting ip daddr @gfwlist tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft delete rule inet v2ray output ip daddr @gfwlist tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft delete rule inet v2ray prerouting ip daddr ${LOCAL_IP} udp dport ${CHINADNS_MIN_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft delete rule inet v2ray output ip daddr ${LOCAL_IP} udp dport ${CHINADNS_MIN_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft delete rule inet v2ray prerouting ip daddr @gfwlist udp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft delete rule inet v2ray output ip daddr @gfwlist udp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
}

disable_v2ray_rules() {
    if nft list table inet v2ray 2>/dev/null >/dev/null; then
        nft flush table inet v2ray
    else
        nft add table inet v2ray
    fi
    
    # 创建或清空 set：gfwlist
    if nft list set inet v2ray gfwlist 2>/dev/null >/dev/null; then
        nft delete set inet v2ray gfwlist
    fi

    # 创建 gfwlist 集合
    nft add set inet v2ray gfwlist { type ipv4_addr\;}
    set_multi_domestic_dns
    echo "ingfw" > /tmp/v2raymode.txt
    
}

stop_service()  {
    echo "[+] 停止 v2ray 服务"
    disable_v2ray_rules
}

enable_v2ray_rules(){
    running_v2ray_mode=$(cat /tmp/v2raymode.txt 2>/dev/null | tr -d '\r')
    v2ray_mode=`uci get advancedconfig.@rules[0].v2raymode 2>/dev/null`

    if [ x${v2ray_mode} = x${running_v2ray_mode} ]; then
        echo "[+] v2ray模式未变化"
    else
        echo "[+] v2ray模式已变化"
        echo "[+] 设置${v2ray_mode}模式中"
        if [ "${v2ray_mode}" = "outlands" ]; then
            disable_gfwlist_firewall_rules
            create_bypasslist
            enable_bypasslist_firewall_rules
            set_multi_foreign_dns
        
        elif [ "${v2ray_mode}" = "gfwlist" ]; then
            disable_bypasslist_firewall_rules
            create_gfwlist
            enable_gfwlist_firewall_rules
            set_multi_foreign_dns
        
        elif [ "${v2ray_mode}" = "ingfw" ]; then
            disable_v2ray_rules
        fi
        echo "${v2ray_mode}" > /tmp/v2raymode.txt
    fi
}

start_service()  {
    echo "[+] 启动 v2ray 服务"
    mkdir -p /var/log/v2ray
    ulimit -n 65535
    procd_open_instance
    procd_set_param command $V2RAY_BIN run -config $V2RAY_CONF
    procd_set_param file $V2RAY_CONF
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_set_param pidfile /var/run/v2ray.pid
    enable_v2ray_rules
    procd_close_instance
}

service_triggers() {
    procd_add_reload_trigger "advancedconfig"
}
      

```

2)修改/etc/dnsmasq.d/下的conf文件：

将原来的所有

```bash

ipset=/xxxx.com/gfwlist

```

全部修改为：

```bash

nftset=/xxxx.com/4#inet#v2ray#gfwlist

```

需要注意的是，conf文件不能有windows换行符，因为nftset对于格式非常敏感，之前windows换行符对于ipset没有问题，但是对于nftset就无法正常执行。

3）对应的/etc/config/chinadns文件：

```bash

config chinadns
	option chnroute '/etc/chinadns_chnroute.txt'
	option addr '0.0.0.0'
	option enable '1'
	option port '5355'
	option bidirectional '0'
	option server '114.114.114.114,127.0.0.1:5354'

```

4）对应的/root/start_multi_chinadns.sh文件：

```bash

#!/bin/sh
# 启动多个 chinadns 实例并使用不同的国内 DNS 和端口
# 依赖：chinadns、v2ray、dnsmasq-full、coreutils-nohup

killall chinadns 2>/dev/null
/etc/init.d/chinadns restart
sleep 1

start_chinadns() {
  local port=$1
  local dns=$2
  local v2port=$3
  nohup /usr/bin/chinadns -m -b 0.0.0.0 -p "$port" \
    -s "$dns",127.0.0.1:"$v2port" -c /etc/chinadns_chnroute.txt \
    >/dev/null 2>&1 &
  sleep 1
}

start_chinadns 5357 119.29.29.29 5356
start_chinadns 5359 223.5.5.5    5358
start_chinadns 5361 180.76.76.76 5360

```

5）对应的/etc/config/v2ray配置：

```bash

{
  "inbounds": [
    {    
      "protocol": "dokodemo-door",
      "port": 1060,
      "listen":"0.0.0.0",
      "sniffing": {
        "enabled": false,
        "destOverride": ["http", "tls"]
      },
       "settings": {
         "network": "tcp,udp",
         "followRedirect": true 
       }
    },
    {
      "protocol": "dokodemo-door",
      "listen":"0.0.0.0",
      "port": 5354,
      "settings": {
        "address": "8.8.8.8",
        "port": 53,
        "network": "udp",
        "timeout": 0,
        "followRedirect": false
      }
    },
    {
      "protocol": "dokodemo-door",
      "listen":"0.0.0.0",
      "port": 5356,
      "settings": {
        "address": "8.8.8.8",
        "port": 53,
        "network": "udp",
        "timeout": 0,
        "followRedirect": false
      }
    },
    {
      "protocol": "dokodemo-door",
      "listen":"0.0.0.0",
      "port": 5358,
      "settings": {
        "address": "1.1.1.1",
        "port": 53,
        "network": "udp",
        "timeout": 0,
        "followRedirect": false
      }
    },
    {
      "protocol": "dokodemo-door",
      "listen":"0.0.0.0",
      "port": 5360,
      "settings": {
        "address": "8.8.4.4",
        "port": 53,
        "network": "udp",
        "timeout": 0,
        "followRedirect": false
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "vless",
      "tag": "proxy",
      "settings": {
        "vnext": [
          {
            "address": "xxx.com", #需改为实际网址
            "port": 443,
            "users": [
              {
                "id": "UUID", #需改为实际UUID
                "encryption": "none"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "wsSettings": {
          "path": "/path"  #需改为实际路径
        },
        "tcpSettings": {
          "allowInsecureCiphers": false
        }
      }
    }
  ]
}


```




参考：
1.chatgpt
2.https://www.abcde.im/archives/112.html
