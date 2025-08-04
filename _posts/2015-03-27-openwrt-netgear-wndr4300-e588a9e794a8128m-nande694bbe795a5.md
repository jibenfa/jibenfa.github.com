---
id: 260
title: Openwrt netgear wndr4300 利用128M NAND攻略
date: 2015-03-27 16:58:20+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
转载自：http://blog.csdn.net/zhiyuan411/article/details/41399273 ，有修改

最新的barrier_breaker 14.07 op装在 netgear wndr4300以后，可用的rootfs只有约12M，其实这个路由器有128M NAND，剩下的90多兆都分在了/dev/mtdblock11上，为了利用这些空间，让opkg软件能装到这90M里面，就要进行简单的设置：

1.安装软件，准备格式化分区

<pre class="lang:sh decode:true " >#支持mkfs.ext2、mkfs.ext3、mkfs.ext4等命令
opkg install e2fsprogs
#支持ext2、ext3、ext4等分区
opkg install kmod-fs-ext4
mkfs.ext4 /dev/mtdblock11
mkdir /local
mount -t ext4 /dev/mtdblock11  /local -o rw,sync</pre>

2.编辑/etc/rc.local，使得挂载自启动（但是rc.local优先级较低，如果将重要的软件安装在里面可能导致无法启动加载，所以执行后续步骤前现在rootfs 12M空间里面装好需要优先启动的软件，例如block-mount等）

<pre class="lang:sh decode:true " >mount -t ext4 /dev/mtdblock11  /local -o rw,sync</pre>

3.编辑/etc/opkg.conf

<pre class="lang:sh decode:true " >dest local /local</pre>

4.编辑/etc/profile

<pre class="lang:sh decode:true " >export PATH=/usr/bin:/usr/sbin:/bin:/sbin:/local/bin:/local/usr/bin:/local/sbin:/local/usr/sbin
export LD_LIBRARY_PATH=/local/lib:/local/usr/lib

alias opkg='opkg -d local'</pre>

5.使得修改立即生效

<pre class="lang:sh decode:true " >source /etc/profile
mkdir /local/usr/share
# /local/usr目录下建立链接：
ln -s /usr/share /local/usr/share
# /local目录下建立链接：
mkdir /local/etc
ln -s /etc /local/etc
mkdir /local/www
ln -s /www /local/www</pre>

6.接着装个软件试试，应该都装到了local目录了

<pre class="lang:sh decode:true " >opkg install kmod-nls-iso8859-1 kmod-nls-utf8  # 安装语言组件iso-8859-1和utf8
opkg install libncurses
/bin/opkg -d root install luci-app-commands #安装luci界面的shell执行工具，luci相关的内容必须在/目录下安装，然后重启路由器才能生效</pre>