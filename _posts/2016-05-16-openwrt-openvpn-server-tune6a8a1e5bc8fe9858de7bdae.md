---
id: 539
title: Openwrt路由上的Openvpn Server Tun模式配置和firewall配置
date: 2016-05-16 22:03:34+00:00
author: coffeecat
layout: post
categories:
- openwrt
- 科学上网
tags:
- openwrt
- 科学上网
---
之前折腾tun模式好久，总是连上以后要么上不了网，要么根本不走vpn。。。这次抽空总算搞定了。。。  
由于安卓机上的openvpn客户端不支持tap，所以必须要设置tun模式：  
首先是服务器端（openwrt路由）：  
/etc/config/network配置加一个interface：

<pre class="lang:vim decode:true " >config interface 'vpn'
    option proto 'none'
    option ifname 'tun0'</pre>

/etc/config/openvpn配置文件

注意下面10.8.0.0千万不要写成和内网（172.24.8.0）一样，否则会使得路由器变砖！！！

<!--more-->

<pre class="lang:vim decode:true " >config openvpn 'tun_test'
        option port '3366'
        option proto 'tcp'
        option dev 'tun'
        option dev 'tun0'
        option ca '/etc/openvpn/ca.crt'
        option cert '/etc/openvpn/server.crt'
        option key '/etc/openvpn/server.key'
        option dh '/etc/openvpn/dh1024.pem'
        option server '10.8.0.0 255.255.255.0'
        option ifconfig  '10.8.0.1 255.255.255.0'

        option cipher     'AES-256-CBC'
        option ifconfig_pool_persist '/tmp/ipp2.txt'
        option duplicate_cn '1'
        option client_to_client '1'
        option keepalive '10 120'
        option comp_lzo 'yes'
        option persist_key '1'
        option persist_tun '1'
        option status '/tmp/openvpn-status2.log'
        option verb '3'
        option enabled '1'
        option topology 'subnet'
        list push 'topology subnet'
        list push 'dhcp-option DNS 172.24.8.1'
        list push 'dhcp-option WINS 172.24.8.1'
        list push 'redirect-gateway def1'
        #list push 'route-gateway dhcp'
        list push 'route 172.24.8.0 255.255.255.0'</pre>

服务器端/etc/config/firewall配置(涉及vpn的部分)

<pre class="lang:vim decode:true " >#这zone是在原来的lan zone上修改
#--- Add: option masq '1' ---#
config zone
	option name 'lan'
	option input 'ACCEPT'
	option output 'ACCEPT'
	option network 'lan'
	option forward 'DROP'
	option masq '1'


config zone
	option name 'vpn'
	option input 'ACCEPT'
	option forward 'ACCEPT'
	option output 'ACCEPT'
	list network 'vpn'
	list subnet '10.8.0.0/24'
	option masq '0'
	option mtu_fix '1'

config forwarding
	option dest 'lan'
	option src 'vpn'

config forwarding
	option dest 'vpn'
	option src 'lan'


config rule
	option name 'OpenVPN-Access'
	option src 'wan'
	option dest_port '3366'
	option family 'ipv4'
	option target 'ACCEPT'
	option proto 'tcp udp'

#--- Once Assigned a VPN IP, Allow Inbound Traffic to LAN ---#
# LuCI: From IP range 10.8.0.0/24 in any zone To IP range 172.24.8.0/24 
# on this device (Accept Input)
config rule
	option target 'ACCEPT'
	option proto 'tcp udp'
	option family 'ipv4'
	option src '*'
	option src_ip '10.8.0.0/24'
	option dest_ip '172.24.8.0/24'
	option name 'Allow Inbound VPN Traffic to LAN'
 
#--- Once Assigned a VPN IP, Allow Forwarded Traffic to LAN ---#
# LuCI: From IP range 10.8.0.0/24 in any zone To IP range 172.24.8.0/24 
# on this device (Accept Forward)
config rule
	option target 'ACCEPT'
	option proto 'tcp udp'
	option family 'ipv4'
	option src '*'
	option src_ip '10.8.0.0/24'
	option dest '*'
	option dest_ip '172.24.8.0/24'
	option name 'Allow Forwarded VPN Traffic to LAN'
 
#--- Allow Outbound ICMP Traffic from VPN ---#
# LuCI: ICMP From IP range 10.8.0.0/24 in any zone To any host in lan 
# (Accept Forward)
config rule
	option target 'ACCEPT'
	option proto 'icmp'
	option src_ip '10.8.0.0/24'
	option src '*'
	option dest 'lan'
	option name 'Allow Inbound ICMP Traffic from VPN to LAN'

#--- Allow Outbound Ping Requests from VPN ---#
# LuCI: ICMP with type echo-request From IP range 10.8.0.0/24 in any
# zone To any host in wan (Accept Forward)
config rule
	option target 'ACCEPT'
	option proto 'icmp'
	option src '*'
	option src_ip '10.8.0.0/24'
	option dest 'wan'
	option name 'Allow Outbound ICMP Echo Request (8) from VPN'
	list icmp_type 'echo-request'

#--- Allow forwarding from VPN to WAN ---#
config forwarding
	option dest 'wan'
	option src 'vpn'

</pre>

自定义防火墙规则：  
iptables -I INPUT 1 -p tcp &#8211;dport 1194 -j ACCEPT  
iptables -I INPUT 1 -p udp &#8211;dport 1194 -j ACCEPT  
iptables -I INPUT 1 -p tcp &#8211;dport 3366 -j ACCEPT  
iptables -I INPUT 1 -p udp &#8211;dport 3366 -j ACCEPT

安卓客户端配置文件，test.ovpn:

<pre class="lang:vim decode:true " >client
dev tun
proto tcp
connect-retry-max 5
connect-retry 5

auth-nocache
remote 路由的外网ip或者ddns 3366  
resolv-retry infinite
nobind
float
persist-key
persist-tun
ns-cert-type server
comp-lzo
verb 3
cipher		AES-256-CBC
mssfix		0
tun-mtu		24000

&lt;ca&gt;
-----BEGIN CERTIFICATE-----
此处省略xxx字
-----END CERTIFICATE-----
&lt;/ca&gt;

&lt;cert&gt;
-----BEGIN CERTIFICATE-----
此处省略xxx字
-----END CERTIFICATE-----
&lt;/cert&gt;

&lt;key&gt;
-----BEGIN PRIVATE KEY-----
此处省略xxx字
-----END PRIVATE KEY-----
&lt;/key&gt;
</pre>

如果openvpn服务器和chinadns、ss客户端部署在一个国内路由器上，会发现10.8.0.0/24网段虽然能够获得正确的dns，但是无法访问谷歌之类的网站，所以需要手动进行配置，编写 openvpn.firewall文件：

<pre class="lang:vim decode:true " >#!/bin/sh

#Date:     2016-05-18

#create a new chain named SHADOWSOCKSXX
iptables -t nat -N SHADOWSOCKSXX

# Ignore your shadowsocks server's addresses
# It's very IMPORTANT, just be careful.

iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d vps的ip地址 -p tcp -j RETURN

# Ignore LANs IP address,redirect to adbyby
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d 0.0.0.0/8 -p tcp -j RETURN
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d 10.0.0.0/8 -p tcp -j RETURN
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d 127.0.0.0/8 -p tcp -j RETURN
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d 169.254.0.0/16 -p tcp -j RETURN
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d 172.16.0.0/12 -p tcp -j RETURN
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d 192.168.0.0/16 -p tcp -j RETURN
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d 224.0.0.0/4 -p tcp -j RETURN
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d 240.0.0.0/4 -p tcp -j RETURN
 
# Ignore China IP address
for white_ip in `cat /etc/chinadns_chnroute.txt`;
do
    iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -d "${white_ip}" -p tcp -j RETURN

done

# Anything else should be redirected to shadowsocks's local port
iptables -t nat -A SHADOWSOCKSXX -s 10.8.0.0/24 -p tcp -j DNAT --to-destination 172.24.8.1:1180
# Apply the rules
iptables -t nat -A PREROUTING -s 10.8.0.0/24 -p tcp -j SHADOWSOCKSXX</pre>

然后：

<pre class="lang:sh decode:true " >chmod +x openvpn.firewall</pre>

每次启动的时候运行就是了。。。

参考：  
1.https://wiki.openwrt.org/doc/howto/openvpn-streamlined-server-setup  
2.https://blog.zencoffee.org/2014/05/building-vpn-openvpn-openwrt/  
3.https://www.loganmarchione.com/2015/08/openwrt-with-openvpn-server-on-tp-link-archer-c7/#Configure_networkfirewall