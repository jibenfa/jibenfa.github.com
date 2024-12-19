---
id: 782
title: openwrt路由部署wireguard实现两地组网
date: 2024-12-19T09:39:31+00:00
author: coffeecat
layout: post


categories:


---
很久没升级路由了，最近openwrt和openvpn又更新版本了，导致之前的openwrt路由下opevpn互联配置出了些问题，连同Windows下tap模式访问局域网也失效了，配了半天都未成功，只能使用tun模式。

然后研究了一下wireguard，发现配置比openvpn简单太多了。。。记录一下备忘：

<pre lang="bash" line="0"  colla="+">
opkg update
opkg install luci-app-wireguard kmod-wireguard wireguard-tools
</pre>



参考：

1.https://www.knightli.com/2022/04/14/openwrt-wireguard-connect-two-network/
2.chatgpt

