---
id: 781
title: openwrt下解决dnsmasq cannot access directory 的问题
date: 2024-12-18 09:39:31+00:00
author: coffeecat
layout: post
categories: &id001
- openwrt
tags: *id001
---
最近更新了openwrt版本，结果设置dnsmasq-full的时候发现无法启动dnsmasq，查日志发现有个报错：
<pre lang="bash" line="0"  colla="+">
daemon.crit dnsmasq[1]: cannot access directory /etc/dnsmasq.d: No such file or directory
</pre>
明明已经设置该文件夹为777权限了，还是有这个问题，后来查阅资料发现openwrt 22.03.0版本后，限制了dnsmasq的文件夹访问权限。

处理方式是：

1.将/etc/dnsmasq.conf下的配置注释掉或者删掉：
<pre lang="bash" line="0"  colla="+">
#conf-dir=/etc/dnsmasq.d
</pre>
2.在/etc/config/dhcp的配置文件中的dnsmasq配置中增加一条：

<pre lang="bash" line="0"  colla="+">
config dnsmasq
	...
 	option confdir '/etc/dnsmasq.d'
	...
</pre>
3.重启dnsmasq服务即可。


参考：

1.https://github.com/openwrt/openwrt/issues/10625