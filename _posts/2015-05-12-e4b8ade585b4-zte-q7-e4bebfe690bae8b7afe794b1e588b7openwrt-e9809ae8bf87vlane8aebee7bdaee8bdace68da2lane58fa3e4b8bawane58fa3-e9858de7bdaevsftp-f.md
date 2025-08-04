---
id: 334
title: 中兴 ZTE Q7 便携路由刷Openwrt + 通过vlan设置转换lan口为wan口 + 配置vsftpd ftp服务器攻略
date: 2015-05-12 20:52:54+00:00
author: coffeecat
layout: post
categories: &id001
- openwrt
tags: *id001
---
买了不少便携路由，都觉得性能不够或者细节不能忍，逛op官网的时候偶尔发现这个神器，于是买了回来，果然好，强烈推荐这个便携出差路由：中兴ZTE Q7，理由：  
1.免拆机免ttl刷openwrt，op官方支持，3g无线中继，lan口可改wan，  
2.强大的mt7620a处理器搭配8m flash，64m ddr2内存，秒杀市面绝大多数的便携路由，  
3.内置锂聚合物电池，可以当充电宝，也可独立为3g网卡供电，充电时亦可带3g网卡上网，  
4.支持sd卡扩展，可架设ftp服务器，swap内存扩展，迅雷离线等等。  
5.便宜！之前x东 69活动没赶上，现在89也是便宜到家的，小米路由mini虽flash和内存比它大，但是无电池，不便携，价格要139。

刷了SS +chinadns+ adbyby+ vsftp以后很爽。。  
<!--more-->

1)免拆机免ttl刷openwrt的攻略可以参考[恩山上的文章](http://www.right.com.cn/forum/forum.php?mod=viewthread&tid=162767)  
简单来说是  
1.telnet登陆q7，默认ip是192.168.1.254，用户名和密码是admin和opendoor（瀑布汗的密码）  
2.刷入[恩山H大的breed](http://www.right.com.cn/forum/thread-161906-1-1.html)：把u盘用fat32分区以后拷贝 插入usb口，在q7的telnet命令行下运行mount，就可以看到u盘mount路径例如/media/sdp1/，然后运行：

<pre class="lang:sh decode:true " >mtd_write -r -e mtd1 write /media/sdp1/breed-mt7620-zte-q7.bin mtd1</pre>

然后等几分钟。。这个breed是H大搞出来的替代不死uboot的东东，非常之好用！

3.到openwrt官网[下载q7固件](https://downloads.openwrt.org/snapshots/trunk/ramips/mt7620/openwrt-ramips-mt7620-zte-q7-squashfs-sysupgrade.bin)，然后把q7关机，用牙签戳reset键开机，待红灯快速闪几下后断开，然后用浏览器访问192.168.1.1，找到固件更新，刷入该固件。

2)刷完以后就不用多说了，telnet 192.168.1.1，然后装上luci以后[装科学上网套件](https://routeragency.com/?p=175)，并[安装和配置zte mf190 3g上网卡](https://routeragency.com/?p=236)

3)然后安装SD读卡器驱动，以便识别SD卡：

<pre class="lang:sh decode:true " >opkg install kmod-sdhci-mt7620</pre>

装的同时会安装几个dependent的软件，例如kmod-sdhci和kmod-mmc  
装完以后插入sd卡或者带套的tf卡，我是把tf卡分2个区，ext4的2.6G，swap的1.2G  
重启完q7路由后就会发现在/dev下多了几个mmc开头的东东，其中mmcblk0p1就是我的2.6G的ext4分区，mmcblk0p5是1.2G的swap分区，然后运行

<pre class="lang:sh decode:true " >block detect &gt; /etc/config/fstab
mkdir /mnt/anonymous
vi /etc/config/fstab</pre>

修改为（uuid每个人的不一样，不改）：

<pre class="lang:vim decode:true " >config global
	option anon_swap '0'
	option anon_mount '0'
	option auto_swap '1'
	option auto_mount '1'
	option delay_root '5'
	option check_fs '0'

config mount
	option uuid '0c033b6b-9d12-4fa9-8b0f-9c68988a9f1c'
	option enabled '1'
	option target '/mnt/anonymous'

config swap
	option device '/dev/mmcblk0p5'
	option enabled '1'</pre>

4）安装vsftpd

<pre class="lang:sh decode:true " >opkg install vsftpd
vi /etc/vsftpd.conf
</pre>

修改为：

<pre class="lang:tsql decode:true " >background=YES
listen=YES

#允许匿名用户
ftp_username=nobody
#允许匿名访问
anonymous_enable=YES
#允许匿名用户上传、下载和新建文件夹
anon_upload_enable=YES
anon_world_readable_only=NO
anon_mkdir_write_enable=YES
#不允许修改所属
chown_https://jibenfa.github.io/uploads=NO
#chown_username=nobody
#设置匿名用户根目录
anon_root=/mnt/anonymous
#限制匿名用户上传、下载速度
anon_max_rate=512000
#允许本地用户登录
local_enable=YES
#允许上传
write_enable=YES
local_umask=022
check_shell=NO
#设置本地用户主目录
local_root=/mnt
#限制用户只能访问主目录
chroot_local_user=yes
accept_timeout=60
idle_session_timeout=300
max_clients=600
max_per_ip=5
#dirmessage_enable=YES
ftpd_banner=Welcome to Coffeecat FTP service.
session_support=NO
#不记录日志，注释掉
#syslog_enable=YES
#xferlog_enable=YES
#xferlog_file=/var/log/vsftpd.log
#xferlog_std_format=YES</pre>

<pre class="lang:sh decode:true " >chmod -R 557 /mnt/anonymous 
chmod a-w /mnt/anonymous/
</pre>

5）修改lan口为wan口（注意，这一步操作前必须开启wifi，否则将无法再访问路由器设置界面！！！！！！！！！只能再次刷机！！！！慎重！！！！）,这里参考了[恩山论坛文章](http://www.right.com.cn/Forum/thread-164504-1-1.html)

<pre class="lang:sh decode:true " >vi /etc/config/network</pre>

修改为（注意我改了默认网关IP为：172.24.0.1）：

<pre class="lang:vim decode:true " >config interface 'loopback'
	option ifname 'lo'
	option proto 'static'
	option ipaddr '127.0.0.1'
	option netmask '255.0.0.0'

config globals 'globals'
	option ula_prefix 'fd37:04f5:111b::/48'

config interface 'lan'
	option ifname 'eth0.1'
	option force_link '1'
	option macaddr '08:12:62:62:ad:24'
	option type 'bridge'
	option proto 'static'
	option netmask '255.255.255.0'
	option ip6assign '60'
	option ipaddr '172.24.0.1'

config interface 'wan'
        option ifname 'eth0.2'
        option proto 'dhcp'

config switch
        option name 'switch0'
        option reset '1'
        option enable_vlan '1'

config switch_vlan
        option device 'switch0'
        option vlan '1'
        option ports '0 1 2 3 5 6t'
        option vid '1'

config switch_vlan
        option device 'switch0'
        option vlan '2'
        option ports '6t 4'
        option vid '2'

config interface '3g'
	option proto '3g'
	option device '/dev/ttyUSB2'
	option service 'umts'
	option apn '3gnet'
	option dialnumber '*99#'


</pre>

重启路由生效，lan口变为wan口