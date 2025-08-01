---
id: 588
title: Openwrt 利用squid进行上网行为控制，过滤在线视频和视频下载
date: 2016-08-11T08:30:42+00:00
author: coffeecat
layout: post


categories:


---
某些情况下，需要过滤在线视频和视频下载，按照IP或者网址过滤当然是可以的，不过要找到那么多视频网址很麻烦，现在大多数视频网站都开启了CDN，即便拿到ip池也是不全的。找了半天，终于看到了一个办法。  
首先当然是安装squid了：

<pre class="lang:sh decode:true " >opkg update
opkg install squid
vi /etc/squid/squid.conf</pre>

内容为：

<!--more-->

<pre class="lang:vim decode:true " >######General Settings##############

http_port 3128 transparent

######Block Video Streaming##############

acl media rep_mime_type video/flv video/x-flv
acl media rep_mime_type -i ^video/
acl media rep_mime_type -i ^video\/
#acl media rep_mime_type ^application/x-shockwave-flash
acl media rep_mime_type ^application/vnd.ms.wms-hdr.asfv1
acl media rep_mime_type ^application/x-fcs
acl media rep_mime_type ^application/x-mms-framed
acl media rep_mime_type ^video/x-ms-asf
acl media rep_mime_type ^audio/mpeg
acl media rep_mime_type ^audio/x-scpls
acl media rep_mime_type ^video/x-flv
acl media rep_mime_type ^video/mpeg4
acl media rep_mime_type ms-hdr
acl media rep_mime_type x-fcs
acl mediapr urlpath_regex \.flv(\?.*)?$
acl mediapr urlpath_regex -i \.(avi|mp4|mov|m4v|mkv|flv)(\?.*)?$
acl mediapr urlpath_regex -i \.(mpg|mpeg|avi|mov|flv|wmv|mkv|rmvb)(\?.*)?$


acl localnet src 172.16.0.0/12
acl localnet src 192.168.0.0/16
acl localnet src fc00::/7
acl localnet src fe80::/10

acl ssl_ports port 443

acl safe_ports port 80
acl safe_ports port 21
acl safe_ports port 443
acl safe_ports port 70
acl safe_ports port 210
acl safe_ports port 1025-65535
acl safe_ports port 280
acl safe_ports port 488
acl safe_ports port 591
acl safe_ports port 777
acl connect method connect


http_access deny mediapr
http_reply_access deny media

http_access deny !safe_ports
http_access deny connect !ssl_ports

http_access allow localhost manager
http_access deny manager

http_access deny to_localhost

http_access allow localnet
http_access allow localhost

http_access deny all

refresh_pattern ^ftp: 1440 20% 10080
refresh_pattern ^gopher: 1440 0% 1440
refresh_pattern -i (/cgi-bin/|\?) 0 0% 0
refresh_pattern . 0 20% 4320

access_log none
cache_mem 16 MB
cache_log /dev/null
cache_store_log /dev/null
logfile_rotate 0

logfile_daemon /dev/null</pre>

然后在防火墙打开重定向：

<pre class="lang:sh decode:true " >iptables -t nat -A PREROUTING -p tcp -s 192.168.1.0/24 --dport 80 -j REDIRECT --to-ports 3128
#iptables -t nat -A PREROUTING -p tcp -s 192.168.1.0/24 --dport 443 -j REDIRECT --to-ports 3128
iptables -t nat -A PREROUTING -p tcp -s 192.168.1.0/24 --dport 1024:65535 -j REDIRECT --to-ports 3128
</pre>

注意443端口重定向可能会造成网页无法访问。

最后启动squid:

<pre class="lang:sh decode:true " >/etc/init.d/squid start</pre>

参考：  
1.https://rbgeek.wordpress.com/2012/09/12/how-to-block-video-streaming-with-squid/