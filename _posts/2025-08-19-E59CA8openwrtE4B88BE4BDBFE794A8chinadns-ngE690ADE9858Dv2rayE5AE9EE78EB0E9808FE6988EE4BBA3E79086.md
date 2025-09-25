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

1）从<a href="https://github.com/zfl9/chinadns-ng/releases/tag/2025.08.09">github</a>下载的现成的二进制文件，需注意CPU架构要匹配（之前自己编译openwrt下的chinadns-ng版本未成功。。。联机编译网络环境太差了，另外openwrt下的源码版本有点老，不支持很多新特性，所以还是用原版的靠谱）。把二进制文件拷贝到/usr/bin下。

改名为chinadns-ng，并附加执行权限：
```bash
mv chinadns-ng+wolfssl@aarch64-linux-musl@generic+v8a@fast+lto /usr/bin/chinadns-ng
chmod +x /usr/bin/chinadns-ng
```
运行一下：
```bash
/usr/bin/chinadns-ng -V
```
如果显示正常就ok了

2）从<a href="https://github.com/zfl9/chinadns-ng">github</a>下载source，提取其中的res文件夹下的文件，拷贝到/etc/chinadns-ng文件夹下，没有的话就创建一个，主要有以下几个文件：

```vim
 # ls /etc/chinadns-ng
chains.nftset             chnroute.nftset           direct.txt                disable_gfwip.nftset      gfwip6.nftset             reservedip6.nftset        update-chnroute-nft.sh    update-chnroute6.sh
chnlist.txt               chnroute6.ipset           disable_chnroute.nftset   disable_gfwip6.nftset     gfwlist.txt               update-all.sh             update-chnroute.sh        update-gfwlist.sh
chnroute.ipset            chnroute6.nftset          disable_chnroute6.nftset  gfwip.nftset              reservedip.nftset         update-chnlist.sh         update-chnroute6-nft.sh

```
注意：
direct.txt,
disable_chnroute.nftset,
disable_chnroute6.nftset,
gfwip.nftset,
gfwip6.nftset,
disable_gfwip.nftset,
disable_gfwip6.nftset
chains.nftset
reservedip.nftset
reservedip6.nftset
是我创建的，后面细说。

建议启用前通过update*.sh进行更新

a) 其中direct.txt中内容为需要通过国内dns解析的域名，主要是v2ray服务端域名！这一点非常重要，v2ray服务端域名要直接由国内dns解析，否则可能无法连接。例如v2ray服务端域名是xxx.com，则direct.txt内容可以为：

```vim

ntp.org
vultur.com
xxx.com

```
这里可以不手工添加xxx.com，因为后面v2ray_chinadnsng的脚本也会读取v2ray配置文件然后自动添加的。

b) disable_chnroute.nftset内容为：
```bash
flush set inet global chnroute
```

c) disable_chnroute6.nftset内容为：
```bash
flush set inet global chnroute6
```
d) gfwip.nftset内容为：
```bash
add table inet global
add set inet global gfwip { type ipv4_addr;flags interval; }
```

e) gfwip6.nftset内容为：
```bash
add table inet global
add set inet global gfwip6 { type ipv4_addr;flags interval; }
```

f) disable_chnroute.nftset内容为：
```bash
flush set inet global gfwip
```

g) disable_chnroute6.nftset内容为：
```bash
flush set inet global gfwip6
```

h) chains.nftset内容为：
```bash
add table inet global

add chain inet global prerouting { type nat hook prerouting priority dstnat; }
add chain inet global output { type nat hook output priority -100; }

flush chain inet global prerouting
flush chain inet global output
```

i) reservedip.nftset内容为：
```bash
add table inet global

# 定义 IPv4 本地/保留网段
define ipv4_localnet = {
    0.0.0.0/8,          # 本网络/未指定
    10.0.0.0/8,         # 私有网络
    100.64.0.0/10,      # CGNAT / Carrier-grade NAT
    127.0.0.0/8,        # 回环地址
    169.254.0.0/16,     # 链路本地 / APIPA
    172.16.0.0/12,      # 私有网络
    192.0.0.0/24,       # IETF 协议保留
    192.0.2.0/24,       # 文档/示例地址 (TEST-NET-1)
    192.88.99.0/24,     # 6to4 中继（已废弃）
    192.168.0.0/16,     # 私有网络
    198.18.0.0/15,      # 测试网络
    198.51.100.0/24,    # 文档/示例地址 (TEST-NET-2)
    203.0.113.0/24,     # 文档/示例地址 (TEST-NET-3)
    224.0.0.0/4,        # 多播
    240.0.0.0/4         # 未来保留 已经包含 255.255.255.255
}

add set inet global localnet { type ipv4_addr; flags interval; elements = $ipv4_localnet; }

```

j) reservedip6.nftset内容为：
```bash
add table inet global

# 定义 IPv6 本地/保留网段
define ipv6_localnet = {
    ::/128,             # 未指定地址
    ::1/128,            # 回环地址
    ::ffff:0:0/96,      # IPv4 映射
    64:ff9b::/96,       # IPv4/IPv6 NAT64
    100::/64,           # 丢弃用途
    fc00::/7,           # 唯一本地地址 (ULA)
    fe80::/10,          # 链路本地
    ff00::/8            # 多播
}

add set inet global localnet6 { type ipv6_addr; flags interval; elements = $ipv6_localnet; }

```

2.配置chinadns-ng

1）创建并修改配置文件/etc/config/chinadns-ng:
```vim

# 监听地址和端口
bind-addr 0.0.0.0
bind-port 5353

# 国内 DNS
china-dns tls://101.226.4.6
china-dns tls://223.5.5.5
china-dns tls://223.6.6.6
china-dns tls://1.12.12.12
china-dns tls://120.53.53.53

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
group-upstream tls://223.5.5.5,tls://1.12.12.12
group-ipset inet@global@chnroute,inet@global@chnroute6

# 收集 tag:chn、tag:gfw 域名的 IP (可选)
# 相关 family，table，set名称要与nftset文件中的一致，否则无法生效
# 我这里只动态收集gfwlist（tag:gfw）里网址解析出来的gfwip和gfwip6，应用于v2ray的gfwlist模式中
#add-tagchn-ip inet@global@chnip,inet@global@chnip6
add-taggfw-ip inet@global@gfwip,inet@global@gfwip6

# 测试 tag:none 域名的 IP (针对国内上游)
# 相关 family，table，set名称要与nftset文件中的一致，否则无法生效
ipset-name4 inet@global@chnroute
ipset-name6 inet@global@chnroute6

# dns 缓存
cache 4096
cache-stale 86400
cache-refresh 20

# verdict 缓存 (用于 tag:none 域名)
verdict-cache 4096
```

2.配置v2ray

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

2）调整启动脚本（/etc/init.d/v2ray_chinadnsng）
```bash
#!/bin/sh /etc/rc.common
#
# This is free software, licensed under the GNU General Public License v3.
# See /LICENSE for more information.
#
# To use this file, install chinadns-ng,v2ray,knot-dig(only for test) first
#
#

START=90
USE_PROCD=1

V2RAY_BIN="/usr/bin/v2ray"
V2RAY_CONF="/etc/config/v2ray.json"
V2RAY_PORT="1060"

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

#从v2ray的配置文件中读取网址，放到chinadns-ng的直接解析文件中，避免因无法解析导致无法连接到服务端
add_v2ray_domain_to_direct_group() {
    direct_file=${CHINADNSNG_FILES_PATH}${DIRECT_GROUP_FILE}
    . /usr/share/libubox/jshn.sh
    json_load_file "${V2RAY_CONF}"
    json_select outbounds
    json_select 1
    json_select settings
    json_select vnext
    json_select 1
    json_get_var addr address
    if [ -s "${direct_file}" ]; then 
        if grep -q "${addr}" "${direct_file}"; then
            echo "[+] v2ray域名已经存在于${direct_file}"
        else
            echo "[+] 将v2ray域名添加到${direct_file}"
            if [ "$(tail -c 1 ${direct_file})" != "" ]; then
                # 最后一行没有换行符，先补一个
                printf '\n' >> ${direct_file}
            fi
            echo ${addr} >> ${direct_file}
        fi
    else
        echo "[+] 创建${direct_file}，将v2ray域名添加到${direct_file}"
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
    #抽检，如果表中没有添加保留地址，则退出，避免无法连接路由器本机
    if ! nft list table inet global | grep -q "0.0.0.0"; then
        echo "[!] 致命错误，保留地址集添加失败，设置失败，请检查${CHINADNSNG_FILES_PATH}${RESERVEDIP_NFT_NAME}"
        return 1
    fi
    nft add rule inet global prerouting ip daddr != @chnroute tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet global output ip daddr != @chnroute tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet global prerouting ip6 daddr != @chnroute6 tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet global output ip6 daddr != @chnroute6 tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
}

enable_gfwip_nft_rules(){
    create_chain_rules
    nft add rule inet global prerouting ip daddr @gfwip tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet global output ip daddr @gfwip tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet global prerouting ip6 daddr @gfwip6 tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
    nft add rule inet global output ip6 daddr @gfwip6 tcp dport 0-65535 counter redirect to :${V2RAY_PORT} 2>/dev/null
}

disable_nft_rules() {
    create_empty_chain
    nft -f ${CHINADNSNG_FILES_PATH}${DISABLE_CHNROUTE_NFT_NAME} 2>/dev/null
    nft -f ${CHINADNSNG_FILES_PATH}${DISABLE_CHNROUTE6_NFT_NAME} 2>/dev/null
    nft -f ${CHINADNSNG_FILES_PATH}${DISABLE_GFWIP_NFT_NAME} 2>/dev/null
    nft -f ${CHINADNSNG_FILES_PATH}${DISABLE_GFWIP6_NFT_NAME} 2>/dev/null
    set_multi_domestic_dns
    echo "ingfw" > /tmp/v2raymode.txt   
}

stop_service()  {
    echo "[+] 停止 v2ray 服务"
    disable_nft_rules
}

enable_nft_rules(){
    running_v2ray_mode=$(cat /tmp/v2raymode.txt 2>/dev/null | tr -d '\r')
    v2ray_mode=`uci get advancedconfig.@rules[0].v2raymode 2>/dev/null`

    if [ x${v2ray_mode} = x${running_v2ray_mode} ]; then
        echo "[+] v2ray模式未变化"
    else
        disable_nft_rules
        add_v2ray_domain_to_direct_group
        if [ "${v2ray_mode}" = "outlands" ]; then
            echo "[+] 设置${v2ray_mode}（境外全局代理模式）模式中"
            append_chnroute_list
            enable_chnroute_nft_rules
            set_multi_foreign_dns
        
        elif [ "${v2ray_mode}" = "gfwlist" ]; then
            echo "[+] 设置${v2ray_mode}（白名单代理模式）模式中"
            append_gfwip_list
            enable_gfwip_nft_rules
            set_multi_foreign_dns
        
        elif [ "${v2ray_mode}" = "ingfw" ]; then
            echo "[+] 设置墙内访问模式"
        fi
        echo "${v2ray_mode}" > /tmp/v2raymode.txt
    fi
}

start_service()  {
    enable_nft_rules
    echo "[+] 启动 chinadns-ng 服务"
    procd_open_instance
    procd_set_param command $CHINADNSNG_BIN -C $CHINADNSNG_CONF
    procd_set_param respawn
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
    sleep 2

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
    procd_close_instance
}

service_triggers() {
    procd_add_reload_trigger "advancedconfig"
}

```

然后执行：
```bash
chmod +x /etc/init.d/v2ray_chinadnsng
/etc/init.d/v2ray_chinadnsng enable
```

3.调整dnsmasq，chinadns等配置，避免冲突。

```bash
echo '' > /etc/dnsmasq.conf
/etc/init.d/chinadns disable
/etc/init.d/v2ray disable
rm /root/start_multi_chinadns.sh
```

然后在luci界面中，把“网络->dhcp/dns->转发”菜单下的dns转发改成“127.0.0.1#5353”，保存后重启openwrt。


参考：

1.https://github.com/zfl9/chinadns-ng

2.chatgpt
