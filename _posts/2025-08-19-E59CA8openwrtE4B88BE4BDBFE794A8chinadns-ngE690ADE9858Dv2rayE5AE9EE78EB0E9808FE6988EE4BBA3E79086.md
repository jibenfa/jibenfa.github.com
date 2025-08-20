---
id: 824
title: 在openwrt下使用chinadns-ng搭配v2ray实现透明代理
date: 2025-08-19 00:12:13+00:00
author: coffeecat
layout: post
categories:
- 科学上网
tags:
- chinadns-ng
- openwrt
- v2ray
---

之前在openwrt下一直用chinadns、dnsmasq搭配v2ray实现的透明代理上网，但是chinadns很久没维护了，另外看到了chinadns-ng，除了支持原版chinadns的功能外，还能实现dns over tcp/tls，按域名、ip分流，ipv6，还支持dns缓存，最新版本已经可以全面替代dnsmasq，dns查询性能大幅度提升。所以研究了一下，部署以后通过cdn warp后的代理速度明显提升，访问github网页速度提升了约40-50%。

下面是部署的步骤：

1.下载chinadns-ng

1）从https://github.com/zfl9/chinadns-ng/releases/tag/2025.08.09 下载的现成的（自己编译openwrt下的chinadns-ng版本未成功。。。）。拷贝到/usr/bin下，并改名为chinadns-ng，
然后：
```bash
chmod +x /usr/bin/chinadns-ng
```
运行一下：
```bash
/usr/bin/chinadns-ng -V
```
如果显示正常就ok了

2）从https://github.com/zfl9/chinadns-ng 中下载source，提取其中的res文件夹下的文件，拷贝到/etc/chinadns-ng文件夹下，没有的话就创建一个，主要有以下几个文件：

```vim
# ls /etc/chinadns-ng/
chnlist.txt               chnroute6.ipset           direct.txt                disable_gfwip.nftset      gfwip6.nftset             update-chnroute-nft.sh    update-chnroute6-nft.sh
chnroute.ipset            chnroute6.nftset          disable_chnroute.nftset   disable_gfwip6.nftset     gfwlist.txt               update-chnroute-v2ray.sh  update-chnroute6.sh
chnroute.nftset           chnroute_v2ray.txt        disable_chnroute6.nftset  gfwip.nftset              update-chnlist.sh         update-chnroute.sh        update-gfwlist.sh
```
注意：direct.txt,update-chnroute-v2ray.sh,chnroute_v2ray.txt,disable_chnroute.nftset,disable_chnroute6.nftset,gfwip.nftset,gfwip6.nftset,,disable_gfwip.nftset,disable_gfwip6.nftset是我创建的。

a)其中direct.txt中内容为需要通过国内114解析的域名，主要是v2ray的域名！这一点非常重要，v2ray域名一定要由国内dns解析，否则无法连接。例如v2ray服务端域名是xxx.com，则direct.txt内容可以为：

```vim
xxx.com
ntp.org
vultur.com
```
b)update-chnroute-v2ray.sh主要用于拉取国内ip段，生成chnroute_v2ray.txt，内容为：
```bash
#!/bin/bash
set -o errexit
set -o pipefail

# exit if curl failed
data="$(curl -4fsSkL https://raw.githubusercontent.com/pexcn/daily/gh-pages/chnroute/chnroute.txt)"
echo "" >chnroute_v2ray.txt
echo "$data" | awk '{printf("%s\n", $0)}' >>chnroute_v2ray.txt
```
其实chnroute_v2ray.txt内容和之前chinadns的chinadns_chnroute.txt是一毛一样的，主要用于v2ray。

c)disable_chnroute.nftset内容为：
```bash
flush set inet global chnroute
```

d)disable_chnroute6.nftset内容为：
```bash
flush set inet global chnroute6
```
e)gfwip.nftset内容为：
```bash
add table inet global
add set inet global gfwip { type ipv4_addr;flags interval; }
```

f)gfwip6.nftset内容为：
```bash
add table inet global
add set inet global gfwip8 { type ipv4_addr;flags interval; }
```

g)disable_chnroute.nftset内容为：
```bash
flush set inet global gfwip
```

h)disable_chnroute6.nftset内容为：
```bash
flush set inet global gfwip6
```

2.配置chinadns-ng

1）创建并修改配置文件/etc/config/chinadns-ng:
```vim

# 监听地址和端口
bind-addr 127.0.0.1
bind-port 5353

# 国内 DNS
china-dns 114.114.114.114
china-dns 223.5.5.5
china-dns 119.29.29.29

# 国外 DNS
trust-dns 127.0.0.1#5354
trust-dns tcp://127.0.0.1#5356
trust-dns 127.0.0.1#5358
trust-dns 127.0.0.1#5360

# 列表文件
chnlist-file /etc/chinadns-ng/chnlist.txt
gfwlist-file /etc/chinadns-ng/gfwlist.txt

# group文件
group direct
group-dnl /etc/chinadns-ng/direct.txt
group-upstream 114.114.114.114

# 收集 tag:chn、tag:gfw 域名的 IP (可选)
#add-tagchn-ip inet@global@chnip,inet@global@chnip6
add-taggfw-ip inet@global@gfwip,inet@global@gfwip6

# 测试 tag:none 域名的 IP (针对国内上游)
ipset-name4 inet@global@chnroute
ipset-name6 inet@global@chnroute6

# dns 缓存
cache 4096
cache-stale 86400
cache-refresh 20

# verdict 缓存 (用于 tag:none 域名)
verdict-cache 4096
```



2）注册为系统服务

创建并编辑/etc/init.d/chinadns-ng
```bash
#!/bin/sh /etc/rc.common
# init script for chinadns-ng

START=95
STOP=10

USE_PROCD=1
PROG=/usr/bin/chinadns-ng
CONF=/etc/config/chinadns-ng

enable_nft_rules (){
    nft -f /etc/chinadns-ng/chnroute.nftset
    nft -f /etc/chinadns-ng/chnroute6.nftset
    nft -f /etc/chinadns-ng/gfwip.nftset
    nft -f /etc/chinadns-ng/gfwip6.nftset
}

disable_nft_rules (){
    nft -f /etc/chinadns-ng/disable_chnroute.nftset
    nft -f /etc/chinadns-ng/disable_chnroute6.nftset
    nft -f /etc/chinadns-ng/disable_gfwip.nftset
    nft -f /etc/chinadns-ng/disable_gfwip6.nftset
}

start_service() {
    [ -x "$PROG" ] || exit 1
    [ -f "$CONF" ] || exit 1
    echo "[+] 启动 chinadns-ng 服务"
    procd_open_instance
    procd_set_param command $PROG -C $CONF
    procd_set_param respawn
    enable_nft_rules
    procd_close_instance
}

stop_service()  {
    echo "[+] 停止 chinadns-ng 服务"
    disable_nft_rules
}
```
然后执行：
```bash
chmod +x /etc/init.d/chinadns-ng
/etc/init.d/chinadns-ng enable
/etc/init.d/chinadns-ng start
```

3.配置v2ray

1）修改配置文件（/etc/config/v2ray.json）
```vim
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
        "network": "tcp",
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
            "address": "xxx.com",
            "port": 443,
            "users": [
              {
                "id": "***************uuid************************",
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
          "path": "/mypath"
        },
        "tcpSettings": {
          "allowInsecureCiphers": false
        }
      }
    }
  ]
}

```

2）调整启动脚本（/etc/init.d/v2ray）
```bash
#!/bin/sh /etc/rc.common
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.
#
# To use this file, install chinadns-ng,v2ray,coreutils-nohup,coreutils-paste first
#
#!/bin/sh /etc/rc.common

START=90
USE_PROCD=1

DOMAIN="xxx.com"
DNS_SERVER="114.114.114.114"
BACKUP_DNS_SERVER="119.29.29.29 223.5.5.5 180.76.76.76"
LOCAL_IP="127.0.0.1"
#CHINADNSNG和V2RAY端口范围:5353-5361，须搭配对应的chinadnsng和v2ray配置文件使用
CHINADNSNG_PORT="5353"
CHINADNSNG_FILES_PATH="/etc/chinadns-ng/"
CHNROUTE_NFT_NAME="chnroute.nftset"
CHNROUTE6_NFT_NAME="chnroute6.nftset"
GFWIP_NFT_NAME="gfwip.nftset"
GFWIP6_NFT_NAME="gfwip6.nftset"
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
        echo "[+] 设置使用ChinaDNSNG DNS服务器"
        chinadnsng_listen_ipport=${LOCAL_IP}"#"${CHINADNSNG_PORT}
        uci -q delete dhcp.@dnsmasq[0].server
        uci add_list dhcp.@dnsmasq[0].server=${chinadnsng_listen_ipport}
        uci set dhcp.@dnsmasq[0].noresolv=1
        uci set dhcp.@dnsmasq[0].nohosts=1
        uci commit dhcp
        echo "[+] 重启dnsmasq服务"
        /etc/init.d/dnsmasq restart 1>/dev/null 2>&1
        echo "[✓] 完成"
    fi
}

create_chnroute() {   
    echo "[*] 创建 inet global 表和 chnroute 集合" #注意这里的inet global chnroute要和chnroute.nftset中inet global chnroute的一致

    #add table inet global
    #add set inet global chnroute { type ipv4_addr; flags interval; }
    #add element inet global chnroute { 1.0.1.0/24 }
    nft -f ${CHINADNSNG_FILES_PATH}${CHNROUTE_NFT_NAME}
    nft -f ${CHINADNSNG_FILES_PATH}${CHNROUTE6_NFT_NAME}

    # 添加私有地址段，注意这里的inet global chnroute要和chnroute.nftset中的一致
    echo "[+] 添加内网地址段到 chnroute"
    nft add element inet global chnroute  { \
        0.0.0.0/8, 10.0.0.0/8, 127.0.0.0/8, \
        169.254.0.0/16, 172.16.0.0/12, \
        192.168.0.0/16, 224.0.0.0/4, 240.0.0.0/4 \
    }

    # 加载 VPS 域名解析结果
    echo "[+] 解析 $DOMAIN 并加入 chnroute"
    for ip in $(dig +short "$DOMAIN" @"$DNS_SERVER" | grep -Eo '([0-9]{1,3}\.){3}[0-9]{1,3}'); do
        nft add element inet global chnroute { $ip }
        echo "    加入 $ip"
    done
    echo "    chnroute 已载入 $(nft list set inet global chnroute | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(/[0-9]+)?' | wc -l) 条目"

}

create_gfwip(){
    echo "[*] 创建 inet global 表和 gfwip 集合"

    nft -f ${CHINADNSNG_FILES_PATH}${GFWIP_NFT_NAME}
    nft -f ${CHINADNSNG_FILES_PATH}${GFWIP6_NFT_NAME}

}

enable_chnroute_firewall_rules(){
    # 创建 nat 类型链
    nft list chain inet global prerouting 1>/dev/null 2>&1 || nft add chain inet global prerouting { type nat hook prerouting priority dstnat\; }
    nft list chain inet global output 1>/dev/null 2>&1 || nft add chain inet global output { type nat hook output priority -100\; }
    nft flush chain inet global prerouting 2>/dev/null
    nft flush chain inet global output 2>/dev/null
    nft add rule inet global prerouting ip daddr ${LOCAL_IP} tcp dport ${CHINADNSNG_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet global prerouting ip daddr ${LOCAL_IP} udp dport ${CHINADNSNG_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet global output ip daddr ${LOCAL_IP} tcp dport ${CHINADNSNG_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet global output ip daddr ${LOCAL_IP} udp dport ${CHINADNSNG_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet global prerouting ip daddr != @chnroute tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet global output ip daddr != @chnroute tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
}

enable_gfwip_firewall_rules(){
    # 创建 nat 类型链
    nft list chain inet global prerouting 1>/dev/null 2>&1 || nft add chain inet global prerouting { type nat hook prerouting priority dstnat\; }
    nft list chain inet global output 1>/dev/null 2>&1 || nft add chain inet global output { type nat hook output priority -100\; }
    nft flush chain inet global prerouting 2>/dev/null
    nft flush chain inet global output 2>/dev/null
    nft add rule inet global prerouting ip daddr ${LOCAL_IP} tcp dport ${CHINADNSNG_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet global prerouting ip daddr ${LOCAL_IP} udp dport ${CHINADNSNG_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet global output ip daddr ${LOCAL_IP} tcp dport ${CHINADNSNG_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet global output ip daddr ${LOCAL_IP} udp dport ${CHINADNSNG_PORT}-${V2RAY_MAX_DNS_PORT} return 2>/dev/null
    nft add rule inet global prerouting ip daddr @gfwip tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet global output ip daddr @gfwip tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null

}

disable_v2ray_rules() {
    nft flush chain inet global prerouting 2>/dev/null
    nft flush chain inet global output 2>/dev/null
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
            disable_v2ray_rules
            create_chnroute
            enable_chnroute_firewall_rules
            set_multi_foreign_dns
        
        elif [ "${v2ray_mode}" = "gfwlist" ]; then
            disable_v2ray_rules
            create_gfwip
            enable_gfwip_firewall_rules
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

4.调整dnsmasq，chinadns等配置，避免冲突。

```bash
echo '' > /etc/dnsmasq.conf
/etc/init.d/chinadns disable
/etc/init.d/chinadns stop
rm /root/start_multi_chinadns.sh
```

然后在luci界面中，把“网络->dhcp/dns->转发”菜单下的dns转发改成“127.0.0.1#5353”，保存后重启openwrt。


参考：
1.https://github.com/zfl9/chinadns-ng
2.chatgpt
