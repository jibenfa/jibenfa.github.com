---
id: 204
title: Debian 7 下比较aggressive的网络加速软件net_speeder
date: 2015-03-07 20:13:07+00:00
author: coffeecat
layout: post
categories:
- linux
tags:
- linux
---
https://github.com/snooda/net-speeder 的开源项目。  
在高延迟不稳定链路上优化单线程下载速度

注1：开启了net-speeder的服务器上对外ping时看到的是4倍，实际网络上是2倍流量。另外两倍是内部dup出来的，不占用带宽。 另外，内部dup包并非是偷懒未判断。。。是为了更快触发快速重传的。 注2：net-speeder不依赖ttl的大小，ttl的大小跟流量无比例关系。不存在windows的ttl大，发包就多的情况。

也就是说利用2倍发包，实现下载速度提升，这样带宽消耗也是2倍。。。

debian/ubuntu安装libnet，libpcap，libnet1-dev，libpcap-dev：

```sh
apt-get install libnet1

apt-get install libpcap0.8 

apt-get install libnet1-dev

apt-get install libpcap0.8-dev 
```

然后下载build.sh和net_speeder.c到/root/net-speeder，编译：

```sh
chmod +x build.sh
sh build.sh
```

运行：

```sh
nohup /root/net-speeder/net_speeder eth0 "ip" >/dev/null 2>&1 & 
```