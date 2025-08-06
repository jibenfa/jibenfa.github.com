---
id: 648
title: 开关openwrt/lede路由上的usb设备电源
date: 2017-10-11 22:25:43+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
最近搞了个华为的usb无线网卡E8372插在lede路由上，但是想实现程序控制其供电，查阅资料后发现可以这样实现：  
首先：

<pre><code class="language-sh">ls /sys/class/gpio/</code></pre>

<pre><code class="language-vim">export      gpiochip32  unexport    usb3power
gpiochip0   gpiochip64  usb2power</code></pre>

由于网卡是插在usb3的口上。  
于是：  
要打开网卡电源：  
echo 1 > /sys/class/gpio/usb3power/value  
要关闭网卡电源：  
echo 0 > /sys/class/gpio/usb3power/value

上述方法可以利用网卡断电重启来解决因开机时网卡启动慢于路由启动，导致eth1 interface不能正常up的问题。

参考资料：  
https://wiki.openwrt.org/doc/howto/usb.overview