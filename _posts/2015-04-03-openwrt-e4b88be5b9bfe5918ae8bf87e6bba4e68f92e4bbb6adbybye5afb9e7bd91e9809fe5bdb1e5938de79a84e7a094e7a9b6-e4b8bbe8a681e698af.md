---
id: 307
title: Openwrt 下广告过滤插件adbyby对网速影响的研究 ——主要是软nat不给力
date: 2015-04-03 12:18:58+00:00
author: coffeecat
layout: post
categories: &id001
- openwrt
tags: *id001
---
家中电信100Mbps光纤，主路由是netgear wndr4300，刷op前后家里的nas迅雷离线均可以达到11MB/s下载速度，但是路由装上adbyby以后，迅雷离线平均速度不会超过6.2MB/s（50Mbps），经过分析测试，原因在于如下语句：

<pre class="lang:sh decode:true " >iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8118</pre>

由于op目前不支持硬件nat，上述语句的nat是软nat实现，性能较差。  
由于路由上还有ss，所以一般不会用pc主机上迅雷下东西，我将nas ip加入了ss例外列表，同时为了下载提速，将nas ip加入不使用adbyby的nat转发的ip段。  
解决方案：  
将家里分成2个子网，掩码25，低地址段使用静态ip，分配其中一个给nas用于离线下载，高地址段使用dhcp，通过adbyby的nat转发proxy实现广告过滤。路由、nas和客户机的掩码设置为24，这样可以互相访问，千兆局域网。  
首先在luci里面‘网络’-‘接口’-‘lan’-‘DHCP服务器’-‘开始’，将dhcp起始段设为128。

将/etc/rc.local里面的语句修改为：

<pre class="lang:sh decode:true " >iptables -t nat -A PREROUTING -p tcp -s 192.168.1.128/25 --dport 80 -j REDIRECT --to-ports 8118</pre>

重启路由。  
这样，将终端的ip设为小于128的时候，adbyby广告过滤功能对其无效，下载速度100M，当终端大于等于128时，adbyby广告过滤功能又对其开启，下载速度50M。