---
id: 439
title: Openwrt 扫描在线设备并自动关机
date: 2015-08-02 08:32:27+00:00
author: coffeecat
layout: post
categories: &id001
- openwrt
tags: *id001
---
由于懒得在关闭PC或者手机后去关路由器，我写了2个关机脚本：

1.该脚本在局域网没有在线设备时关闭路由器

<pre class="lang:sh decode:true " >vi autoShutDownNoDevs.sh </pre>

<pre class="lang:vim decode:true " >#!/bin/sh

mon() {
while [ "1" ];
do
 sleep 240
 cc=`cat /proc/net/arp | grep 0x2`
 if [ -z "$cc" ];then
     if [ -f /tmp/noshut ];then
        echo ' Shut Down aborted! '
     else
        kill -USR1 1
     fi
 fi
 sleep 60
done
}

mon &</pre>

<pre class="lang:sh decode:true " >chmod +x autoShutDownNoDevs.sh</pre>

2.该脚本在局域网某两台固定IP的PC离线时关闭路由器（防止未关手机wifi时路由器无法关闭）

<pre class="lang:sh decode:true " >vi autoShutDownNoPCs.sh</pre>

<pre class="lang:vim decode:true " >#!/bin/sh
sleep 300
ping -c 1 172.24.1.150 &gt; /dev/null
ret=$?
if [ $ret -eq 0 ]
then
echo ' Shut Down aborted! '
else
ping -c 1 172.24.1.155 &gt;/dev/null
res=$?
if [ $res -eq 0 ]
then
echo ' Shut Down aborted! '
else
if [ -f /tmp/noshut ]
then
echo ' Shut Down aborted! '
else
kill -USR1 1
fi
fi
fi
</pre>

<pre class="lang:sh decode:true " >chmod +x autoShutDownNoPCs.sh</pre>

定时任务

<pre class="lang:vim decode:true " >*/5 22-4 * * * /root/autoShutDownNoPCs.sh</pre>

参考资料：  
1. http://blog.csdn.net/qianguozheng/article/details/28393145