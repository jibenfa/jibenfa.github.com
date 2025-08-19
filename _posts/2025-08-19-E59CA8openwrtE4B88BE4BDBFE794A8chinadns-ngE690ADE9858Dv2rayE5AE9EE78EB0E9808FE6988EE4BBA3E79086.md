---
id: 824
title: 在openwrt下使用chinadns-ng搭配v2ray实现透明代理
date: 2025-08-19 00:12:13+00:00
author: coffeecat
layout: post
categories:
- 科学上网
tags:
- chinadns-ng
- openwrt
- v2ray
---

之前在openwrt下一直用chinadns、dnsmasq搭配v2ray实现的透明代理上网，但是chinadns很久没维护了，另外看到了chinadns-ng，除了支持原版chinadns的功能外，还能实现dns over tcp/tls，按域名、ip分流，还支持dns缓存，最新版本已经可以全面替代dnsmasq，dns查询性能大幅度提升。所以研究了一下，部署以后通过cdn warp后的代理速度明显提升，访问github网页速度提升了约40-50%。

下面是部署的步骤：

1.下载chinadns-ng

1）从https://github.com/zfl9/chinadns-ng/releases/tag/2025.08.09 下载的现成的（自己编译openwrt下的chinadns-ng版本未成功。。。）。拷贝到/usr/bin下，并改名为chinadns-ng，
然后：
```bash
chmod +x /usr/bin/chinadns-ng
```
运行一下：
```bash
/usr/bin/chinadns-ng -V
```
如果显示正常就ok了

2）从https://github.com/zfl9/chinadns-ng 中下载source，提取其中的res文件夹下的文件，拷贝到/etc/chinadns-ng文件夹下，没有的话就创建一个，主要有以下几个文件：

```vim
# ls /etc/chinadns-ng/
chnlist.txt               chnroute6.ipset           direct.txt                gfwlist.txt               update-chnroute-v2ray.sh  update-chnroute6.sh
chnroute.ipset            chnroute6.nftset          disable_chnroute.nftset   update-chnlist.sh         update-chnroute.sh        update-gfwlist.sh
chnroute.nftset           chnroute_v2ray.txt        disable_chnroute6.nftset  update-chnroute-nft.sh    update-chnroute6-nft.sh
```
注意：direct.txt  update-chnroute-v2ray.sh chnroute_v2ray.txt 是我自己创建的后面会说。

2.配置chinadns-ng

1）修改配置文件


2）注册为系统服务

3.配置v2ray

1）修改配置文件

2）调整启动脚本

4.调整dnsmasq，chinadns等配置，避免冲突。
