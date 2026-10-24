---
id: 830
title: 在openwrt下部署xray和reality
date: 2026-10-23 00:15:13+00:00
author: coffeecat
layout: post
categories:
- 科学上网
tags:
- reality
- openwrt
- xray
---

最近研究了一下Xray+Reality，比起v2ray+ws+cdn+tls模式，可以免去维护域名的麻烦和费用。速度也能快一丢丢，缺点是有可能会被封ip。于是尝试进行了部署：

1.服务器端部署xray

1）登录服务器端运行：
```bash
wget https://github.com/XTLS/Xray-core/releases/download/v26.10.21/Xray-linux-64.zip
ls -lh Xray-linux-64.zip
unzip -l Xray-linux-64.zip
```
运行一下：
```bash
install -d -m 755 /usr/local/bin /usr/local/share/xray /usr/local/etc/xray
unzip -oq /root/Xray-linux-64.zip -d /tmp/xray-release
install -m 755 /tmp/xray-release/xray /usr/local/bin/xray
install -m 644 /tmp/xray-release/geoip.dat /tmp/xray-release/geosite.dat /usr/local/share/xray/
 /usr/local/bin/xray version
```
如果显示正常就ok了

2）生成uuid、私钥、公钥、shortid：

```bash
/usr/local/bin/xray uuid
/usr/local/bin/xray x25519
openssl rand -hex 8
```

结果是类似这样的，把以下信息记录下来，特别是私钥：

```vim
uuuu-uuuu-uuuu-uuuuuu         #这是uuid
PrivateKey: *******************************  #这是私钥
Password (PublicKey): xxxxxxxxxxxxxxxxxxx    #这是公钥
Hash32: xxxxxxxxxxxxxxx   
iiiiiiii    #这是shortid

```


3)配置文件：

```bash
nano /usr/local/etc/xray/config.json
```

```vim
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "listen": "0.0.0.0",
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "在此替换为服务器生成的uuid",
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "raw",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "target": "www.microsoft.com:443",
          "xver": 0,
          "serverNames": [
            "www.microsoft.com"
          ],
          "privateKey": "在此替换为服务器生成的私钥",
          "shortIds": [
            "在此替换为服务器生成的shortid"
          ]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom"
    }
  ]
}
```

保存退出后，执行以下命令创建运行账户、设置配置权限，并先检查配置：

```bash
getent group xray >/dev/null || groupadd --system xray
id xray >/dev/null 2>&1 || useradd --system --gid xray --no-create-home --shell /usr/sbin/nologin xray
chown root:xray /usr/local/etc/xray /usr/local/etc/xray/config.json
chmod 750 /usr/local/etc/xray
chmod 640 /usr/local/etc/xray/config.json
/usr/local/bin/xray run -test -config /usr/local/etc/xray/config.json
```

若最后显示 Configuration OK.，说明成功了，接下来创建自启动服务：


```bash
cat >/etc/systemd/system/xray.service <<'EOF'
[Unit]
Description=Xray Service
After=network-online.target
Wants=network-online.target

[Service]
User=xray
Group=xray
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=/usr/local/bin/xray run -config /usr/local/etc/xray/config.json
Restart=on-failure
RestartSec=5
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now xray
systemctl status xray --no-pager -l
ss -lntp | grep ':443'

```

如果出现类似以下输出，则说明xray成功运行了：

```bash
LISTEN 0      4096               *:443             :    users:(("xray",pid=2081,fd=4))
```

2.客户端（openwrt）配置

0)在openwrt路由的ssh界面下运行：

```bash

ubus call system board
cat /etc/openwrt_release
opkg print-architecture 2>/dev/null || apk --print-arch 2>/dev/null

```

查看路由版本，我的是aarch64_cortex-a53，于是下载：

https://github.com/XTLS/Xray-core/releases/download/v26.10.21/Xray-linux-arm64-v8a.zip


解压后上传到/usr/bin/xray文件夹下


1）修改配置文件（/etc/config/xray.json）
```vim
{
  "log": {
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log",
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "protocol": "dokodemo-door",
      "port": 1060,
      "listen": "0.0.0.0",
      "sniffing": {
        "enabled": false,
        "destOverride": ["http", "tls"]
      },
      "settings": {
        "network": "tcp,udp",
        "followRedirect": true
      },
      "streamSettings": {
        "sockopt": {
          "tproxy": "redirect"
        }
      }
    },
    {
      "protocol": "dokodemo-door",
      "listen": "0.0.0.0",
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
      "listen": "0.0.0.0",
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
      "listen": "0.0.0.0",
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
      "listen": "0.0.0.0",
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
            "address": "在此替换为服务器IP",
            "port": 443,
            "users": [
              {
                "id": "在此替换为服务器生成的uuid",
                "encryption": "none",
                "flow": "xtls-rprx-vision"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "raw",
        "security": "reality",
        "realitySettings": {
          "serverName": "www.microsoft.com",
          "fingerprint": "chrome",
          "password": "在此替换为服务器生成的公钥",
          "shortId": "在此替换为服务器生成的shortid",
          "spiderX": ""
        }
      }
    }
  ]
}


```

2）调整启动脚本（/etc/init.d/xray_chinadnsng）

a) 以下是iptables的版本适用于openwrt 23及更低版本：

```bash
#!/bin/sh /etc/rc.common
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.
#
# To use this file, install chinadns-ng,xray,knot-dig(only for test) first
#
#

START=90
USE_PROCD=1

XRAY_BIN="/usr/bin/xray/xray"
XRAY_CONF="/etc/config/xray.json"
XRAY_PORT="1060"

CHINADNSNG_PORT="5353"
CHINADNSNG_FILES_PATH="/etc/chinadns-ng/"
CHINADNSNG_BIN="/usr/bin/chinadns-ng"
CHINADNSNG_CONF="/etc/config/chinadns-ng"

DEFAULT_DNS_SERVER="223.6.6.6"
LOCAL_IP="127.0.0.1"

# 本配置文件中默认参数为：
# set:chnroute,chnroute6,gfwip,gfwip6
# 上述值需与chinadnsng配置文件中的一致，否则无法生效：
# add-taggfw-ip gfwip,gfwip6
# ipset-name4 chnroute
# ipset-name6 chnroute6
CHNROUTE_IPT_NAME="chnroute.ipset"
CHNROUTE6_IPT_NAME="chnroute6.ipset"
#CHAINS_IPT_NAME="chains.ipset"
RESERVEDIP_IPT_NAME="reservedip.ipset"
RESERVEDIP6_IPT_NAME="reservedip6.ipset"
GFWIP_IPT_NAME="gfwip.ipset"
GFWIP6_IPT_NAME="gfwip6.ipset"
DISABLE_CHNROUTE_IPT_NAME="disable_chnroute.ipset"
DISABLE_CHNROUTE6_IPT_NAME="disable_chnroute6.ipset"
DISABLE_GFWIP_IPT_NAME="disable_gfwip.ipset"
DISABLE_GFWIP6_IPT_NAME="disable_gfwip6.ipset"
DIRECT_GROUP_FILE="direct.txt"

# 将 Xray 出站服务器地址加入透明代理旁路，防止 Xray 连接再次被重定向回自己。
add_xray_server_bypass() {
    . /usr/share/libubox/jshn.sh
    json_load_file "${XRAY_CONF}" || return 1
    json_select outbounds || return 1
    json_select 1 || return 1
    json_select settings || return 1
    json_select vnext || return 1
    json_select 1 || return 1
    json_get_var addr address
    [ -n "${addr}" ] || return 1

    case "${addr}" in
        *:*)
            ip6tables -t nat -I GLOBAL_PREROUTING 1 -p tcp -d "${addr}" -j RETURN 2>/dev/null
            ip6tables -t nat -I GLOBAL_OUTPUT 1 -p tcp -d "${addr}" -j RETURN 2>/dev/null
            echo "[+] 已为 Xray IPv6 服务器地址 ${addr} 添加直连旁路"
            ;;
        *[!0-9.]* )
            echo "[+] Xray服务器地址是域名，将由 ChinaDNS-NG direct group 处理：${addr}"
            ;;
        *)
            iptables -t nat -I GLOBAL_PREROUTING 1 -p tcp -d "${addr}" -j RETURN 2>/dev/null
            iptables -t nat -I GLOBAL_OUTPUT 1 -p tcp -d "${addr}" -j RETURN 2>/dev/null
            echo "[+] 已为 Xray IPv4 服务器地址 ${addr} 添加直连旁路"
            ;;
    esac
}
#从xray的配置文件中读取网址，放到chinadns-ng的直接解析文件中，避免因无法解析导致无法连接到服务端
add_xray_domain_to_direct_group() {
    direct_file=${CHINADNSNG_FILES_PATH}${DIRECT_GROUP_FILE}
    . /usr/share/libubox/jshn.sh
    json_load_file "${XRAY_CONF}"  || return 1
    json_select outbounds || return 1
    json_select 1 || return 1
    json_select settings || return 1
    json_select vnext || return 1
    json_select 1 || return 1
    json_get_var addr address
    [ -n "${addr}" ] || return 1
    case "${addr}" in
        *:*) echo "[+] Xray服务器是IPv6地址，不写入域名 direct.txt"; return 0 ;;
        *[!0-9.]* ) ;;
        *) echo "[+] Xray服务器是IPv4地址，不写入域名 direct.txt"; return 0 ;;
    esac
    if [ -s "${direct_file}" ]; then 
        if grep -q "${addr}" "${direct_file}"; then
            echo "[+] xray域名已经存在于${direct_file}"
        else
            echo "[+] 将xray域名添加到${direct_file}"
            if [ "$(tail -c 1 ${direct_file})" != "" ]; then
                # 最后一行没有换行符，先补一个
                printf '\n' >> ${direct_file}
            fi
            echo ${addr} >> ${direct_file}
        fi
    else
        echo "[+] 创建${direct_file}，将xray域名添加到${direct_file}"
        echo ${addr} > ${direct_file}
    fi
}

set_multi_domestic_dns() {
    current_dns_servers_list=`uci get dhcp.@dnsmasq[0].server 2>/dev/null`
    min_len=$(( ${#DEFAULT_DNS_SERVER} < ${#current_dns_servers_list} ? ${#DEFAULT_DNS_SERVER} : ${#current_dns_servers_list} ))
    if [ x${DEFAULT_DNS_SERVER:0:$min_len} != x${current_dns_servers_list:0:$min_len} ]; then
        echo "[+] 设置使用国内DNS服务器"
        uci -q delete dhcp.@dnsmasq[0].server
        uci add_list dhcp.@dnsmasq[0].server=${DEFAULT_DNS_SERVER}
        uci set dhcp.@dnsmasq[0].noresolv=0
        uci set dhcp.@dnsmasq[0].nohosts=0
        uci commit dhcp
        echo "[+] 重启dnsmasq服务"
        /etc/init.d/dnsmasq restart 1>/dev/null 2>&1
    fi
}

set_multi_foreign_dns() {
    current_dns_servers_list=`uci get dhcp.@dnsmasq[0].server 2>/dev/null`
    min_len=$(( ${#LOCAL_IP} < ${#current_dns_servers_list} ? ${#LOCAL_IP} : ${#current_dns_servers_list} ))
    if [ x${LOCAL_IP:0:$min_len} != x${current_dns_servers_list:0:$min_len} ]; then
        echo "[+] 设置使用ChinaDNSNG DNS服务器"
        chinadnsng_addr_port=${LOCAL_IP}"#"${CHINADNSNG_PORT}
        uci -q delete dhcp.@dnsmasq[0].server
        uci add_list dhcp.@dnsmasq[0].server=${chinadnsng_addr_port}
        uci set dhcp.@dnsmasq[0].noresolv=1
        uci set dhcp.@dnsmasq[0].nohosts=1
        uci commit dhcp
        echo "[+] 重启dnsmasq服务"
        /etc/init.d/dnsmasq restart 1>/dev/null 2>&1
    fi
}

create_empty_chain(){
    # 创建 prerouting output 链
    echo "[*] 创建prerouting output 链"
    # global nat hooks
    iptables -t nat -N GLOBAL_PREROUTING 2>/dev/null
    iptables -t nat -N GLOBAL_OUTPUT 2>/dev/null

    iptables -t nat -F GLOBAL_PREROUTING
    iptables -t nat -F GLOBAL_OUTPUT

    iptables -t nat -C PREROUTING -j GLOBAL_PREROUTING 2>/dev/null || \
    iptables -t nat -A PREROUTING -j GLOBAL_PREROUTING

    iptables -t nat -C OUTPUT -j GLOBAL_OUTPUT 2>/dev/null || \
    iptables -t nat -A OUTPUT -j GLOBAL_OUTPUT

    ip6tables -t nat -N GLOBAL_PREROUTING 2>/dev/null
    ip6tables -t nat -N GLOBAL_OUTPUT 2>/dev/null

    ip6tables -t nat -F GLOBAL_PREROUTING
    ip6tables -t nat -F GLOBAL_OUTPUT

    ip6tables -t nat -C PREROUTING -j GLOBAL_PREROUTING 2>/dev/null || \
    ip6tables -t nat -A PREROUTING -j GLOBAL_PREROUTING

    ip6tables -t nat -C OUTPUT -j GLOBAL_OUTPUT 2>/dev/null || \
    ip6tables -t nat -A OUTPUT -j GLOBAL_OUTPUT
}

append_chnroute_list() {
    # 创建 set：chnroute
    echo "[*] 创建chnroute 集合"
    ipset -R <${CHINADNSNG_FILES_PATH}${CHNROUTE_IPT_NAME} 2>/dev/null

    # 创建 set：chnroute6
    echo "[*] 创建chnroute6 集合"
    ipset -R <${CHINADNSNG_FILES_PATH}${CHNROUTE6_IPT_NAME} 2>/dev/null

}

append_gfwip_list(){
    # 创建 set：gfwip
    echo "[*] 创建gfwip 集合"
    ipset -R <${CHINADNSNG_FILES_PATH}${GFWIP_IPT_NAME} 2>/dev/null

    # 创建 set：gfwip6
    echo "[*] 创建gfwip6 集合"
    ipset -R <${CHINADNSNG_FILES_PATH}${GFWIP6_IPT_NAME} 2>/dev/null

}


create_chain_rules(){
    create_empty_chain
    echo "[*] 创建 @localnet @localnet6 集"
    ipset -R <${CHINADNSNG_FILES_PATH}${RESERVEDIP_IPT_NAME} 2>/dev/null
    ipset -R <${CHINADNSNG_FILES_PATH}${RESERVEDIP6_IPT_NAME} 2>/dev/null
    iptables -t nat -A GLOBAL_PREROUTING -m set --match-set localnet dst -j RETURN
    ip6tables -t nat -A GLOBAL_PREROUTING -m set --match-set localnet6 dst -j RETURN
    iptables -t nat -A GLOBAL_OUTPUT -m set --match-set localnet dst -j RETURN
    ip6tables -t nat -A GLOBAL_OUTPUT -m set --match-set localnet6 dst -j RETURN
}

enable_chnroute_IPT_rules(){
    create_chain_rules
    add_xray_server_bypass
    #如果表中没有添加保留地址，则退出，避免无法连接路由器本机
    if ! ipset list localnet | grep -q "127.0.0.0"; then
        echo "[!] 致命错误，保留地址集添加失败，设置失败，请检查${CHINADNSNG_FILES_PATH}${RESERVED_IPT_NAME}"
        return 1
    fi

    iptables -t nat -A GLOBAL_PREROUTING -p tcp -m set ! --match-set chnroute dst -j REDIRECT --to-port ${XRAY_PORT} 1>/dev/null 2>&1
    iptables -t nat -A GLOBAL_OUTPUT -p tcp -m set ! --match-set chnroute dst -j REDIRECT --to-port ${XRAY_PORT} 1>/dev/null 2>&1
    ip6tables -t nat -A GLOBAL_PREROUTING -p tcp -m set ! --match-set chnroute6 dst -j REDIRECT --to-port ${XRAY_PORT} 1>/dev/null 2>&1
    ip6tables -t nat -A GLOBAL_OUTPUT -p tcp -m set ! --match-set chnroute6 dst -j REDIRECT --to-port ${XRAY_PORT} 1>/dev/null 2>&1
}

enable_gfwip_IPT_rules(){
    create_chain_rules
    add_xray_server_bypass
    iptables -t nat -A GLOBAL_PREROUTING -p tcp -m set --match-set gfwip dst -j REDIRECT --to-port ${XRAY_PORT} 1>/dev/null 2>&1
    iptables -t nat -A GLOBAL_OUTPUT -p tcp -m set --match-set gfwip dst -j REDIRECT --to-port ${XRAY_PORT} 1>/dev/null 2>&1
    ip6tables -t nat -A GLOBAL_PREROUTING -p tcp -m set --match-set gfwip6 dst -j REDIRECT --to-port ${XRAY_PORT} 1>/dev/null 2>&1
    ip6tables -t nat -A GLOBAL_OUTPUT -p tcp -m set --match-set gfwip6 dst -j REDIRECT --to-port ${XRAY_PORT} 1>/dev/null 2>&1
}

disable_IPT_rules() {
    create_empty_chain
    ipset -R <${CHINADNSNG_FILES_PATH}${DISABLE_CHNROUTE_IPT_NAME} 2>/dev/null
    ipset -R <${CHINADNSNG_FILES_PATH}${DISABLE_CHNROUTE6_IPT_NAME} 2>/dev/null
    ipset -R <${CHINADNSNG_FILES_PATH}${DISABLE_GFWIP_IPT_NAME} 2>/dev/null
    ipset -R <${CHINADNSNG_FILES_PATH}${DISABLE_GFWIP6_IPT_NAME} 2>/dev/null
    set_multi_domestic_dns
    echo "ingfw" > /tmp/xraymode.txt   
}

stop_service()  {
    echo "[+] 停止 xray 服务"
    disable_IPT_rules
}

enable_IPT_rules(){
    running_xray_mode=$(cat /tmp/xraymode.txt 2>/dev/null | tr -d '\r')
    xray_mode=`uci get advancedconfig.@rules[0].v2raymode 2>/dev/null`

    if [ x${xray_mode} = x${running_xray_mode} ]; then
        echo "[+] xray模式未变化"
    else
        disable_IPT_rules
        add_xray_domain_to_direct_group
        if [ "${xray_mode}" = "outlands" ]; then
            echo "[+] 设置${xray_mode}（境外全局代理模式）模式中"
            append_chnroute_list
            enable_chnroute_IPT_rules
            set_multi_foreign_dns
        
        elif [ "${xray_mode}" = "gfwlist" ]; then
            echo "[+] 设置${xray_mode}（白名单代理模式）模式中"
            append_gfwip_list
            enable_gfwip_IPT_rules
            set_multi_foreign_dns
        
        elif [ "${xray_mode}" = "ingfw" ]; then
            echo "[+] 设置墙内访问模式"
        fi
        echo "${xray_mode}" > /tmp/xraymode.txt
    fi
}

start_service()  {
    enable_IPT_rules
    echo "[+] 启动 chinadns-ng 服务"
    procd_open_instance
    procd_set_param command $CHINADNSNG_BIN -C $CHINADNSNG_CONF
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
    sleep 2

    echo "[+] 启动 xray 服务"
    mkdir -p /var/log/xray
    ulimit -n 65535
    procd_open_instance
    procd_set_param command $XRAY_BIN run -config $XRAY_CONF
    procd_set_param file $XRAY_CONF
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_set_param pidfile /var/run/xray.pid
    procd_close_instance
}

service_triggers() {
    procd_add_reload_trigger "advancedconfig"
}

```



b) 以下是nftables版本（适用于openwrt 24及更高版本）：

```bash
#!/bin/sh /etc/rc.common
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.
#
# To use this file, install chinadns-ng,xray,zoneinfo-asia,knot-dig(only for test) first
# ln -sf /usr/share/zoneinfo/Asia/Macau /etc/localtime
#

START=90
USE_PROCD=1

XRAY_BIN="/usr/bin/xray/xray"
XRAY_CONF="/etc/config/xray.json"
XRAY_PORT="1060"

CHINADNSNG_PORT="5353"
CHINADNSNG_FILES_PATH="/etc/chinadns-ng/"
CHINADNSNG_BIN="/usr/bin/chinadns-ng"
CHINADNSNG_CONF="/etc/config/chinadns-ng"

DEFAULT_DNS_SERVER="223.6.6.6"
LOCAL_IP="127.0.0.1"

# 本配置文件中NFT默认参数为：
# family:inet
# table:global
# set:chnroute,chnroute6,gfwip,gfwip6
# 上述值需与chinadnsng配置文件中的一致，否则无法生效：
# add-taggfw-ip inet@global@gfwip,inet@global@gfwip6
# ipset-name4 inet@global@chnroute
# ipset-name6 inet@global@chnroute6
# 且下列NFTSET文件中相关 family，table，set名称要也与chinadnsng配置文件中的一致，否则无法生效
CHNROUTE_NFT_NAME="chnroute.nftset"
CHNROUTE6_NFT_NAME="chnroute6.nftset"
CHAINS_NFT_NAME="chains.nftset"
RESERVEDIP_NFT_NAME="reservedip.nftset"
RESERVEDIP6_NFT_NAME="reservedip6.nftset"
GFWIP_NFT_NAME="gfwip.nftset"
GFWIP6_NFT_NAME="gfwip6.nftset"
DISABLE_CHNROUTE_NFT_NAME="disable_chnroute.nftset"
DISABLE_CHNROUTE6_NFT_NAME="disable_chnroute6.nftset"
DISABLE_GFWIP_NFT_NAME="disable_gfwip.nftset"
DISABLE_GFWIP6_NFT_NAME="disable_gfwip6.nftset"
DIRECT_GROUP_FILE="direct.txt"

# 服务器地址为 IP 时，在透明代理重定向前放行，防止 Xray 连接自身形成回环。
add_xray_server_bypass() {
    . /usr/share/libubox/jshn.sh
    json_load_file "${XRAY_CONF}" || return 1
    json_select outbounds || return 1
    json_select 1 || return 1
    json_select settings || return 1
    json_select vnext || return 1
    json_select 1 || return 1
    json_get_var addr address
    json_get_var port port
    [ -n "${addr}" ] && [ -n "${port}" ] || return 1

    case "${addr}" in
        *:*)
            nft add rule inet global prerouting ip6 daddr "${addr}" tcp dport "${port}" return 2>/dev/null
            nft add rule inet global output ip6 daddr "${addr}" tcp dport "${port}" return 2>/dev/null
            echo "[+] 已为 Xray IPv6 服务器地址 ${addr}:${port} 添加 nftables 直连旁路"
            ;;
        *[!0-9.]* )
            echo "[+] Xray服务器地址是域名，依靠 direct.txt 直连解析：${addr}"
            ;;
        *)
            nft add rule inet global prerouting ip daddr "${addr}" tcp dport "${port}" return 2>/dev/null
            nft add rule inet global output ip daddr "${addr}" tcp dport "${port}" return 2>/dev/null
            echo "[+] 已为 Xray IPv4 服务器地址 ${addr}:${port} 添加 nftables 直连旁路"
            ;;
    esac
}

# 域名形式的 Xray 服务器地址加入 ChinaDNS-NG direct group，避免解析走代理造成回环。
add_xray_domain_to_direct_group() {
    direct_file="${CHINADNSNG_FILES_PATH}${DIRECT_GROUP_FILE}"
    . /usr/share/libubox/jshn.sh
    json_load_file "${XRAY_CONF}" || return 1
    json_select outbounds || return 1
    json_select 1 || return 1
    json_select settings || return 1
    json_select vnext || return 1
    json_select 1 || return 1
    json_get_var addr address
    json_get_var port port
    [ -n "${addr}" ] && [ -n "${port}" ] || return 1

    case "${addr}" in
        *:*) echo "[+] Xray服务器是IPv6地址，无需写入域名 direct.txt"; return 0 ;;
        *[!0-9.]* ) ;;
        *) echo "[+] Xray服务器是IPv4地址，无需写入域名 direct.txt"; return 0 ;;
    esac

    if [ -s "${direct_file}" ]; then
        if grep -Fxq "${addr}" "${direct_file}"; then
            echo "[+] Xray域名已经存在于 ${direct_file}"
        else
            echo "[+] 将Xray域名添加到 ${direct_file}"
            [ -z "$(tail -c 1 "${direct_file}")" ] || printf '\n' >> "${direct_file}"
            printf '%s\n' "${addr}" >> "${direct_file}"
        fi
    else
        echo "[+] 创建 ${direct_file} 并添加Xray域名"
        printf '%s\n' "${addr}" > "${direct_file}"
    fi
}

set_multi_domestic_dns() {
    current_dns_servers_list=`uci get dhcp.@dnsmasq[0].server 2>/dev/null`
    min_len=$(( ${#DEFAULT_DNS_SERVER} < ${#current_dns_servers_list} ? ${#DEFAULT_DNS_SERVER} : ${#current_dns_servers_list} ))
    if [ x${DEFAULT_DNS_SERVER:0:$min_len} != x${current_dns_servers_list:0:$min_len} ]; then
        echo "[+] 设置使用国内DNS服务器"
        uci -q delete dhcp.@dnsmasq[0].server
        uci add_list dhcp.@dnsmasq[0].server=${DEFAULT_DNS_SERVER}
        uci set dhcp.@dnsmasq[0].noresolv=0
        uci set dhcp.@dnsmasq[0].nohosts=0
        uci commit dhcp
        echo "[+] 重启dnsmasq服务"
        /etc/init.d/dnsmasq restart 1>/dev/null 2>&1
    fi
}

set_multi_foreign_dns() {
    current_dns_servers_list=`uci get dhcp.@dnsmasq[0].server 2>/dev/null`
    min_len=$(( ${#LOCAL_IP} < ${#current_dns_servers_list} ? ${#LOCAL_IP} : ${#current_dns_servers_list} ))
    if [ x${LOCAL_IP:0:$min_len} != x${current_dns_servers_list:0:$min_len} ]; then
        echo "[+] 设置使用ChinaDNSNG DNS服务器"
        chinadnsng_addr_port=${LOCAL_IP}"#"${CHINADNSNG_PORT}
        uci -q delete dhcp.@dnsmasq[0].server
        uci add_list dhcp.@dnsmasq[0].server=${chinadnsng_addr_port}
        uci set dhcp.@dnsmasq[0].noresolv=1
        uci set dhcp.@dnsmasq[0].nohosts=1
        uci commit dhcp
        echo "[+] 重启dnsmasq服务"
        /etc/init.d/dnsmasq restart 1>/dev/null 2>&1
    fi
}

append_chnroute_list() {
    # 创建 set：chnroute
    echo "[*] 创建 inet global 表和 chnroute 集合"
    nft -f ${CHINADNSNG_FILES_PATH}${CHNROUTE_NFT_NAME} 2>/dev/null

    # 创建 set：chnroute6
    echo "[*] 创建 inet global 表和 chnroute6 集合"
    nft -f ${CHINADNSNG_FILES_PATH}${CHNROUTE6_NFT_NAME} 2>/dev/null

}

append_gfwip_list(){
    # 创建 set：gfwip
    echo "[*] 创建 inet global 表和 gfwip 集合"
    nft -f ${CHINADNSNG_FILES_PATH}${GFWIP_NFT_NAME} 2>/dev/null

    # 创建 set：gfwip6
    echo "[*] 创建 inet global 表和 gfwip6 集合"
    nft -f ${CHINADNSNG_FILES_PATH}${GFWIP6_NFT_NAME} 2>/dev/null

}

create_empty_chain(){
    # 创建 prerouting output 链
    echo "[*] 创建 inet global 表和 prerouting output 链"
    nft -f ${CHINADNSNG_FILES_PATH}${CHAINS_NFT_NAME} 2>/dev/null
}

create_chain_rules(){
    create_empty_chain
    echo "[*] 创建 inet global 表和 保留地址 @localnet @localnet6 集"
    nft -f ${CHINADNSNG_FILES_PATH}${RESERVEDIP_NFT_NAME} 
    nft -f ${CHINADNSNG_FILES_PATH}${RESERVEDIP6_NFT_NAME} 
    nft add rule inet global prerouting ip daddr @localnet return
    nft add rule inet global prerouting ip6 daddr @localnet6 return
    nft add rule inet global output ip daddr @localnet return
    nft add rule inet global output ip6 daddr @localnet6 return
}

enable_chnroute_nft_rules(){
    create_chain_rules
    add_xray_server_bypass || return 1
    #如果表中没有添加保留地址，则退出，避免无法连接路由器本机
    if ! nft list table inet global | grep -q "0.0.0.0"; then
        echo "[!] 致命错误，保留地址集添加失败，设置失败，请检查${CHINADNSNG_FILES_PATH}${RESERVED_NFT_NAME}"
        return 1
    fi
    nft add rule inet global prerouting ip daddr != @chnroute tcp dport 0-65535 counter redirect to :${XRAY_PORT} 2>/dev/null
    nft add rule inet global output ip daddr != @chnroute tcp dport 0-65535 counter redirect to :${XRAY_PORT} 2>/dev/null
    nft add rule inet global prerouting ip6 daddr != @chnroute6 tcp dport 0-65535 counter redirect to :${XRAY_PORT} 2>/dev/null
    nft add rule inet global output ip6 daddr != @chnroute6 tcp dport 0-65535 counter redirect to :${XRAY_PORT} 2>/dev/null
}

enable_gfwip_nft_rules(){
    create_chain_rules
    add_xray_server_bypass || return 1
    nft add rule inet global prerouting ip daddr @gfwip tcp dport 0-65535 counter redirect to :${XRAY_PORT} 2>/dev/null
    nft add rule inet global output ip daddr @gfwip tcp dport 0-65535 counter redirect to :${XRAY_PORT} 2>/dev/null
    nft add rule inet global prerouting ip6 daddr @gfwip6 tcp dport 0-65535 counter redirect to :${XRAY_PORT} 2>/dev/null
    nft add rule inet global output ip6 daddr @gfwip6 tcp dport 0-65535 counter redirect to :${XRAY_PORT} 2>/dev/null
}

disable_nft_rules() {
    create_empty_chain
    nft -f ${CHINADNSNG_FILES_PATH}${DISABLE_CHNROUTE_NFT_NAME} 2>/dev/null
    nft -f ${CHINADNSNG_FILES_PATH}${DISABLE_CHNROUTE6_NFT_NAME} 2>/dev/null
    nft -f ${CHINADNSNG_FILES_PATH}${DISABLE_GFWIP_NFT_NAME} 2>/dev/null
    nft -f ${CHINADNSNG_FILES_PATH}${DISABLE_GFWIP6_NFT_NAME} 2>/dev/null
    #set_multi_domestic_dns
    #echo "ingfw" > /tmp/xraymode.txt   
}

stop_service()  {
    echo "[+] 停止 xray 服务"
}

enable_nft_rules(){
    running_xray_mode=$(cat /tmp/xraymode.txt 2>/dev/null | tr -d '\r')
    xray_mode=`uci get advancedconfig.@rules[0].v2raymode 2>/dev/null`

    if [ x${xray_mode} = x${running_xray_mode} ]; then
        echo "[+] xray模式未变化"
    else
        disable_nft_rules
		add_xray_domain_to_direct_group
		if [ "${xray_mode}" = "outlands" ]; then
            echo "[+] 设置${xray_mode}（境外全局代理模式）模式中"
            append_chnroute_list
			append_gfwip_list
            enable_chnroute_nft_rules
            set_multi_foreign_dns
        
        elif [ "${xray_mode}" = "gfwlist" ]; then
            echo "[+] 设置${xray_mode}（白名单代理模式）模式中"
            append_chnroute_list
			append_gfwip_list
            enable_gfwip_nft_rules
            set_multi_foreign_dns
        
        elif [ "${xray_mode}" = "ingfw" ]; then
            echo "[+] 设置墙内访问模式"
		    set_multi_domestic_dns 
		fi
        echo "${xray_mode}" > /tmp/xraymode.txt
    fi
}

start_service()  {
    enable_nft_rules
    echo "[+] 启动 chinadns-ng 服务"
    procd_open_instance
    procd_set_param command $CHINADNSNG_BIN -C $CHINADNSNG_CONF
    procd_set_param respawn
    #procd_set_param stdout 1
    procd_set_param stderr 1
	#procd_set_param file /var/log/xray/procd.log
	procd_close_instance
    sleep 2

    echo "[+] 启动 xray 服务"
    mkdir -p /var/log/xray
    ulimit -n 65535
    procd_open_instance
    procd_set_param command $XRAY_BIN run -config $XRAY_CONF
    procd_set_param file $XRAY_CONF
    procd_set_param respawn
    #procd_set_param env TZ=Asia/Shanghai
	#procd_set_param stdout 1
    procd_set_param stderr 1
    #procd_set_param file /var/log/chinands-ng/procd.log
	procd_set_param pidfile /var/run/xray.pid
    procd_close_instance
}

service_triggers() {
    procd_add_reload_trigger "advancedconfig"
}

```

3）启动服务：

```bash
chmod 755 /etc/init.d/xray_chinadnsng

/etc/init.d/v2ray_chinadnsng stop
/etc/init.d/v2ray_chinadnsng disable
/etc/init.d/xray_chinadnsng enable
/etc/init.d/xray_chinadnsng start
```

4）开启bbr（不开的话很慢，还不如v2ray+ws+cdn+tls）：

```bash
sudo bash -c 'cat > /etc/sysctl.d/99-bbr.conf <<EOF
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
EOF'

sudo sysctl --system
```

```bash
sysctl net.ipv4.tcp_congestion_control
```
期望输出：net.ipv4.tcp_congestion_control = bbr

```bash
lsmod | grep bbr
```
如果输出了bbr相关信息就是正常运行了。


参考：

1.chatgpt
