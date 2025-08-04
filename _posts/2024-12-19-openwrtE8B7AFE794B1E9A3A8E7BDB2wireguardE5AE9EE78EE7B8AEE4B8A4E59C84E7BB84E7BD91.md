---
id: 800
title: openwrt路由部署wireguard实现两地组网
date: 2024-12-19 06:12:12+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
很久没升级路由了，最近openwrt和openvpn又更新版本了，导致之前的openwrt路由下opevpn互联配置出了些问题，连同Windows下tap模式访问局域网也失效了，配了半天都未成功，只能使用tun模式。

然后研究了一下wireguard，发现配置比openvpn简单太多了。于是决定用wireguard。

配置方法记录一下备忘：

两个路由：

路由A：具有外网ip和动态域名，内网网段172.24.1.0/24

路由B：无外网ip，内网网段172.24.8.0/24

1.两台路由均执行以下操作：

1）安装wireguard，这里使用的是openwrt 23.05.5版本
<pre lang="bash" line="0"  colla="+">
opkg update
opkg install luci-app-wireguard kmod-wireguard wireguard-tools
</pre>

2）生成公私钥对
<pre lang="bash" line="0"  colla="+">
wg genkey | tee privatekey | wg pubkey > publickey
</pre>

3）调整防火墙（/etc/config/firewall），在末尾增加：
<pre lang="bash" line="0"  colla="+">
config zone
        option name 'wg'
        option input 'ACCEPT'
        option forward 'ACCEPT'
        option output 'ACCEPT'
        option masq '1'
        option mtu_fix '1'
        list network 'wg0'

config forwarding
        option src 'wg'
        option dest 'lan'

config forwarding
        option src 'lan'
        option dest 'wg'

config forwarding
        option src 'wg'
        option dest 'lan'

config rule
        option name 'wireguard'
        option src 'wan'
        option dest '*'
        option dest_port '51820'
        option target 'ACCEPT'

</pre>

2.在路由A上设置网络接口（/etc/config/network），在最后增加：
<pre lang="bash" line="0"  colla="+">
config interface 'wg0'
        option proto 'wireguard'
        option private_key '路由A私钥'
        list addresses '10.168.10.1/24'
        option listen_port '51820'

config wireguard_wg0
        option description 'router'
        option public_key '路由B公钥'
        option persistent_keepalive '25'
        list allowed_ips '10.168.10.3/32'
        list allowed_ips '172.24.8.0/24'

config route
        option interface 'wg0'
        option target '172.24.8.0/24'
        option gateway '10.168.10.1'
        option metric '1'
</pre>

3.在路由B上设置网络接口（/etc/config/network），在最后增加：
<pre lang="bash" line="0"  colla="+">
config interface 'wg0'
        option proto 'wireguard'
        option private_key '路由B私钥'
        list addresses '10.168.10.3/24'
        option listen_port '51820'

config wireguard_wg0
        option description 'router_client1'
        option public_key '路由A公钥'
        option endpoint_host '路由A的ddns域名'
        option endpoint_port '51820'
        option persistent_keepalive '25'
        list allowed_ips '10.168.10.1/32'
        list allowed_ips '172.24.1.0/24'

config route
        option interface 'wg0'
        option target '172.24.1.0/24'
        option gateway '10.168.10.3'
        option metric '1'
</pre>

4.最后重启路由A和路由B，两个路由间的局域网就可以互相访问了

参考：

1.https://www.knightli.com/2022/04/14/openwrt-wireguard-connect-two-network/

2.chatgpt
