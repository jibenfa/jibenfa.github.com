---
id: 829
title: 基于openwrt21.02版本的透明代理（v2ray+chinadnsng）设置
date: 2026-03-12 00:15:13+00:00
author: coffeecat
layout: post
categories:
- 科学上网
tags:
- chinadns-ng
- openwrt
- v2ray
- iptables
- ipset
---

最近买了个5G CPE设备，原厂系统是基于openwrt21.02-snapshot改的，不能安装ipk，白瞎了这么好的硬件。为了能够充分利用，我在原厂系统上部署了v2ray+chinadns-ng的透明代理

下面是部署的步骤（与之前24.x版本类似，只不过这里使用了iptables+ipset，而不是nftables）：

1.下载chinadns-ng

1）从<a href="https://github.com/zfl9/chinadns-ng/releases/tag/2025.08.09">github</a>下载的现成的二进制文件。把二进制文件拷贝到/usr/bin下。

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

2）从<a href="https://github.com/zfl9/chinadns-ng">github</a>下载source，提取其中的res文件夹下的文件，拷贝到/etc/chinadns-ng文件夹下，没有的话就创建一个，主要保留以下几个文件：

```vim
 # ls /etc/chinadns-ng
chnlist.txt              chnroute6.ipset          disable_chnroute.ipset   disable_gfwip6.ipset     gfwlist.txt              update-all.sh            update-chnroute.sh       update-gfwlist.sh
chnroute.ipset           chnroute6.nftset         disable_chnroute6.ipset  gfwip.ipset              reservedip.ipset         update-chnlist.sh        update-chnroute6-nft.sh
chnroute.nftset          direct.txt               disable_gfwip.ipset      gfwip6.ipset             reservedip6.ipset        update-chnroute-nft.sh   update-chnroute6.sh
```
注意：
direct.txt,
disable_chnroute.ipset,
disable_chnroute6.ipset,
gfwip.ipset,
gfwip6.ipset,
disable_gfwip.ipset,
disable_gfwip6.ipset
reservedip.ipset
reservedip6.ipset
是我创建的，后面细说。

建议启用前通过update*.sh进行更新

a) 其中direct.txt中内容为需要通过国内dns解析的域名，主要是v2ray服务端域名！这一点非常重要，v2ray服务端域名要直接由国内dns解析，否则可能无法连接。例如v2ray服务端域名是xxx.com，则direct.txt内容可以为：

```vim

ntp.org
vultur.com
xxx.com

```
这里可以不手工添加xxx.com，因为后面v2ray_chinadnsng的脚本也会读取v2ray配置文件然后自动添加的。

b) disable_chnroute.ipset内容为：
```bash
flush chnroute
```

c) disable_chnroute6.ipset内容为：
```bash
flush chnroute6
```
d) gfwip.ipset内容为：
```bash
create gfwip hash:net family inet hashsize 1024 maxelem 65535 -exist
flush gfwip
```

e) gfwip6.ipset内容为：
```bash
create gfwip6 hash:net family inet hashsize 1024 maxelem 65535 -exist
flush gfwip6
```

f) disable_gfwip.ipset内容为：
```bash
flush gfwip
```

g) disable_gfwip6.ipset内容为：
```bash
flush gfwip6
```

h) reservedip.ipset内容为：
```bash
create localnet hash:net family inet hashsize 1024 maxelem 65535 -exist
flush localnet
add localnet 0.0.0.0/8
add localnet 10.0.0.0/8
add localnet 100.64.0.0/10
add localnet 127.0.0.0/8
add localnet 169.254.0.0/16
add localnet 172.16.0.0/12
add localnet 192.0.0.0/24
add localnet 192.0.2.0/24
add localnet 192.88.99.0/24
add localnet 192.168.0.0/16
add localnet 198.18.0.0/15
add localnet 198.51.100.0/24
add localnet 203.0.113.0/24
add localnet 224.0.0.0/4
add localnet 240.0.0.0/4

```

i) reservedip6.ipset内容为：
```bash
create localnet6 hash:net family inet6 hashsize 1024 maxelem 65535 -exist
flush localnet6
add localnet6 ::/128
add localnet6 ::1/128
add localnet6 ::ffff:0:0/96
add localnet6 64:ff9b::/96
add localnet6 100::/64
add localnet6 fc00::/7
add localnet6 fe80::/10
add localnet6 ff00::/8

```

j)打开官方的chnroute.ipset，把第一行：
```bash
create chnroute hash:net family inet
```
修改为：
```bash
create chnroute hash:net family inet -exist
flush chnroute
```
避免因chnroute已经存在导致后面语句不执行。

k)打开官方的chnroute6.ipset，把第一行：
```bash
create chnroute6 hash:net family inet
```
修改为：
```bash
create chnroute6 hash:net family inet -exist
flush chnroute6
```
避免因chnroute已经存在导致后面语句不执行。

2.配置chinadns-ng

1）创建并修改配置文件/etc/config/chinadns-ng:
```vim

# 监听地址和端口，建议通过防火墙设置把来自wan口的目的端口是bind-port的进行阻断
bind-addr 0.0.0.0
bind-port 5353

# 国内 DNS
#china-dns 114.114.114.114
#china-dns 223.5.5.5
#china-dns 119.29.29.29
china-dns 101.226.4.6
china-dns 223.5.5.5
china-dns 223.6.6.6
china-dns 1.12.12.12
china-dns 120.53.53.53

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
group-upstream 223.5.5.5,1.12.12.12
group-ipset chnroute,chnroute6

# 收集 tag:chn、tag:gfw 域名的 IP (可选)
# 我这里只动态收集gfwlist（tag:gfw）里网址解析出来的gfwip和gfwip6，应用于v2ray的gfwlist模式中
add-taggfw-ip gfwip,gfwip6

# 测试 tag:none 域名的 IP (针对国内上游)
ipset-name4 chnroute
ipset-name6 chnroute6

# dns 缓存
cache 4096
cache-stale 86400
cache-refresh 20

# verdict 缓存 (用于 tag:none 域名)
verdict-cache 4096

```

2.配置v2ray（v2ray的安装可以看<a href="https://wallsee.org/openwrt/%E7%A7%91%E5%AD%A6%E4%B8%8A%E7%BD%91/2019/06/09/v2raye59ca8openwrte4b88be79a84e5ae89e8a385e983a8e7bdb2/">这里</a>）

0)新建/etc/config/advancedconfig，内容为：

```vim

config rules
	option v2raymode 'outlands'

```

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
# To use this file, install chinadns-ng,v2ray  first
#
#

START=90
USE_PROCD=1

V2RAY_BIN="/usr/bin/v2ray/v2ray"
V2RAY_CONF="/etc/config/v2ray.json"
V2RAY_PORT="1060"

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

enable_chnroute_ip_rules(){
    create_chain_rules
    #如果表中没有添加保留地址，则退出，避免无法连接路由器本机
    if ! ipset list localnet | grep -q "127.0.0.0"; then
        echo "[!] 致命错误，保留地址集添加失败，设置失败，请检查${CHINADNSNG_FILES_PATH}${RESERVED_IPT_NAME}"
        return 1
    fi

    iptables -t nat -A GLOBAL_PREROUTING -p tcp -m set ! --match-set chnroute dst -j REDIRECT --to-port ${V2RAY_PORT} 1>/dev/null 2>&1
    iptables -t nat -A GLOBAL_OUTPUT -p tcp -m set ! --match-set chnroute dst -j REDIRECT --to-port ${V2RAY_PORT} 1>/dev/null 2>&1
    ip6tables -t nat -A GLOBAL_PREROUTING -p tcp -m set ! --match-set chnroute6 dst -j REDIRECT --to-port ${V2RAY_PORT} 1>/dev/null 2>&1
    ip6tables -t nat -A GLOBAL_OUTPUT -p tcp -m set ! --match-set chnroute6 dst -j REDIRECT --to-port ${V2RAY_PORT} 1>/dev/null 2>&1
}

enable_gfwip_ip_rules(){
    create_chain_rules
    iptables -t nat -A GLOBAL_PREROUTING -p tcp -m set --match-set gfwip dst -j REDIRECT --to-port ${V2RAY_PORT} 1>/dev/null 2>&1
    iptables -t nat -A GLOBAL_OUTPUT -p tcp -m set --match-set gfwip dst -j REDIRECT --to-port ${V2RAY_PORT} 1>/dev/null 2>&1
    ip6tables -t nat -A GLOBAL_PREROUTING -p tcp -m set --match-set gfwip6 dst -j REDIRECT --to-port ${V2RAY_PORT} 1>/dev/null 2>&1
    ip6tables -t nat -A GLOBAL_OUTPUT -p tcp -m set --match-set gfwip6 dst -j REDIRECT --to-port ${V2RAY_PORT} 1>/dev/null 2>&1
}

disable_ip_rules() {
    create_empty_chain
    ipset -R <${CHINADNSNG_FILES_PATH}${DISABLE_CHNROUTE_IPT_NAME} 2>/dev/null
    ipset -R <${CHINADNSNG_FILES_PATH}${DISABLE_CHNROUTE6_IPT_NAME} 2>/dev/null
    ipset -R <${CHINADNSNG_FILES_PATH}${DISABLE_GFWIP_IPT_NAME} 2>/dev/null
    ipset -R <${CHINADNSNG_FILES_PATH}${DISABLE_GFWIP6_IPT_NAME} 2>/dev/null
    set_multi_domestic_dns
    echo "ingfw" > /tmp/v2raymode.txt   
}

stop_service()  {
    echo "[+] 停止 v2ray 服务"
    disable_ip_rules
}

enable_ip_rules(){
    running_v2ray_mode=$(cat /tmp/v2raymode.txt 2>/dev/null | tr -d '\r')
    v2ray_mode=`uci get advancedconfig.@rules[0].v2raymode 2>/dev/null`

    if [ x${v2ray_mode} = x${running_v2ray_mode} ]; then
        echo "[+] v2ray模式未变化"
    else
        disable_ip_rules
        add_v2ray_domain_to_direct_group
        if [ "${v2ray_mode}" = "outlands" ]; then
            echo "[+] 设置${v2ray_mode}（境外全局代理模式）模式中"
            append_chnroute_list
            enable_chnroute_ip_rules
            set_multi_foreign_dns
        
        elif [ "${v2ray_mode}" = "gfwlist" ]; then
            echo "[+] 设置${v2ray_mode}（白名单代理模式）模式中"
            append_gfwip_list
            enable_gfwip_ip_rules
            set_multi_foreign_dns
        
        elif [ "${v2ray_mode}" = "ingfw" ]; then
            echo "[+] 设置墙内访问模式"
        fi
        echo "${v2ray_mode}" > /tmp/v2raymode.txt
    fi
}

start_service()  {
    enable_ip_rules
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

3.在http://cpe管理地址/cgi-bin/luci/admin/network/dhcp中，把“dns转发”改成“127.0.0.1#5353”，保存后重启cpe路由。

4.如果要在厂商的luci界面中增加配置功能，可以新增2个文件：
1）/usr/lib/lua/luci/model/cbi/厂商配置路径/scinet.lua

```bash

local uci = require "luci.model.uci".cursor()

m=Map("advancedconfig",translate("科学上网"), translate("必须提前安装v2ray，chinadns-ng，否则功能会不正常"))
s2=m:section(TypedSection,"rules","")
s2.addremove=false
s2.anonymous=true
s2:tab("config3", translate("选择v2ray的运行模式"),translate("<p>本模块是选择v2ray的运行模式，支持三种模式：白名单模式，境外全局代理模式，墙内上网模式。<p>"))
c = s2:taboption("config3", ListValue, "v2raymode",nil ,translate("代理模式：白名单模式速度较快，但未添加的被墙网站打不开，境外全局代理模式速度较慢，但所有网站都能打开"))
c:value("gfwlist", translate("白名单模式"))
c:value("outlands", translate("境外全局模式"))
c:value("ingfw", translate("墙内上网模式"))

function c.write(self, section, value)   
    ListValue.write(self, section, value)
    -- 设置值
    uci:set("advancedconfig", "rules", "v2raymode", value)
    -- 保存并提交
    uci:save("advancedconfig")
    uci:commit("advancedconfig")
    if value ~= "ingfw" then
        luci.sys.call("(sleep 1; /etc/init.d/v2ray_chinadnsng restart >/dev/null 2>&1) &")
    else
        luci.sys.call("(sleep 1; /etc/init.d/v2ray_chinadnsng stop >/dev/null 2>&1) &")
    end
end

return m

```

2）/usr/lib/lua/luci/controller/厂商配置路径/scinet.lua文件:

```bash

module("luci.controller.厂商配置路径.scinet", package.seeall)
function index()
        if not nixio.fs.access("/etc/config/advancedconfig") then
                return
        end
        page = entry({"厂商配置路径", "vpn","scinet"}, cbi("厂商配置路径/scinet"), _("科学上网"), 20, true)
        page.icon = 'paper-plane'
	page.show = true

end

```


参考：

1.chatgpt
