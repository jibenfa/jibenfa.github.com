---
id: 200
title: Debian 7 Linode VPS的内核微调——增加Hybla选项和加速调整
date: 2015-03-06 14:02:38+00:00
author: coffeecat
layout: post
categories: &id001
- linux
tags: *id001
---
按照linode官网的内核编译教程，最后在make install的时候总会失败，后来只好放弃，但是因为linode内核不带hybla（hybla可以对高延迟高丢包的网络环境进行加速，特别对于下载等应用比较有效），所以只好另辟蹊径，用相同的内核编译模块加载进去，于是找到了如下教程，我的内核是  
3.18.5-x86_64-linode52  
按教程操作ok。

<!--more-->

出处（转载自复苏老客）( http://www.fslk.net/?p=822 ，该网站已经down了，根据百度cache转载)  
编译Linode内核模块小白教程，以tcp_hybla为例

2014年5月28日 复苏老客  
国情原因，中美线路有时掉包率会很高，导致网站访问速度慢，Linux 机器缺省的TCP协议发包算法是cubic，如果改为hybla，在掉包率高时可以大幅提高访问速度；如果cubic只能流畅观看480p的视频，改为hybla则可以流畅观看720p的视频，效果提升是明显的，但很多朋友不会编译内核模块，写个小白教程供大家参考，照以下几步操作一遍，你会发现编译内核模块原来相当简单。

以下教程每行#后面的为需要输入的命令，操作时需要root权限，需要你会使用vi，我的系统是Ubuntu 12.04.2 LTS，其他Linux系统命令不会差别很大，请按自己的情况修改内核名称。  
1. 查看你的机器内核版本：  
#uname -r  
3.11.6-x86_64-linode35

2. 去 https://www.kernel.org/pub/linux/kernel/v3.0/ 下载相同版本的源码到任意目录，解压  
#mkdir /root/mykernel  
#cd /root/mykernel  
#wget https://www.kernel.org/pub/linux/kernel/v3.0/linux-3.11.6.tar.gz  
#tar xzvf linux-3.11.6.tar.gz

3. 安装内核编译工具  
#apt-get update && apt-get install -y build-essential libncurses5-dev

4. 复制Linode原来的内核编译配置文件到源码根目录，在CONFIG\_TCP\_CONG\_CUBIC=y下面增加一行 CONFIG\_TCP\_CONG\_HYBLA=y，再生成编译模块需要的内核  
#cd linux-3.11.6  
#zcat /proc/config.gz > .config  
#vi .config  
查找CONFIG\_TCP\_CONG\_CUBIC=y，在下面增加一行 CONFIG\_TCP\_CONG\_HYBLA=y，保存  
#make

5. 耐心等待编译内核完成，单核编译大约需15分钟，完成后，进入模块所在的目录，编写Makefile  
#cd net/ipv4/  
#mv Makefile Makefile.old  
#vi Makefile  
以下是Makefle的内容，注意要把KDIR修改为你自己的源码路径，其他则照抄就可以了

\# Makefile for tcp_hybla.ko  
obj-m := tcp_hybla.o  
KDIR := /root/mykernel/linux-3.11.6  
PWD := $(shell pwd)  
default:  
$(MAKE) -C $(KDIR) SUBDIRS=$(PWD) modules

6.进入源码根目录，编译模块  
#cd /root/mykernel/linux-3.11.6/  
#make modules

7.进入到模块所在目录，复制生成的 tcp_hybla.ko 到加载目录，测试加载模块  
#cd /root/mykernel/linux-3.11.6/net/ipv4  
#cp tcp_hybla.ko /root/mykernel/  
#cd /root/mykernel/  
加载前  
#sysctl net.ipv4.tcp\_available\_congestion_control  
net.ipv4.tcp\_available\_congestion_control = cubic reno  
#insmod tcp_hybla.ko  
加载后  
#sysctl net.ipv4.tcp\_available\_congestion_control  
net.ipv4.tcp\_available\_congestion_control = cubic reno hybla  
设置hybla为优先  
#sysctl net.ipv4.tcp\_congestion\_control=hybla

8.设置开机自动加载模块，把tcp\_hybla.ko 复制到 /lib/modules/3.11.6-x86\_64-linode35/kernel/net/ipv4  
#cd /lib/modules/3.11.6-x86_64-linode35  
#mkdir -p kernel/net/ipv4  
#cd kernel/net/ipv4  
#cp /root/mykernel/tcp_hybla.ko ./  
#cd /lib/modules/3.11.6-x86_64-linode35  
#depmod -a （该步骤我执行失败，但是没有影响到hybla自启动）

9.修改/etc/sysctl.conf 开机自动设置hybla为优先  
#vi /etc/sysctl.conf  
net.ipv4.tcp\_congestion\_control = hybla

用这9步就可以了，只是动态加载模块，不用更换内核，不用停机重启，不影响网站正常运营，相当方便，值得尝试，参考这个方法可以为 Linode 动态加载任何需要的内核模块，如fastopen，htcp，highspeed 等，有任何问题请到推上找 @interwebdev ，转载请注明出处( http://www.fslk.net/?p=822 )，谢谢.

另外根据http://shadowsocks.org/en/config/advanced.html 进行了优化

<pre class="lang:sh decode:true " >vi /etc/security/limits.conf</pre>

增加：

<pre class="lang:vim decode:true " >* soft nofile 51200
* hard nofile 51200</pre>

<pre class="lang:sh decode:true " >vi /etc/init.d/shadowsocks</pre>

增加

<pre class="lang:vim decode:true " >ulimit -n 51200</pre>

<pre class="lang:sh decode:true " >fs.file-max = 51200

net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.core.rmem_default = 65536
net.core.wmem_default = 65536
net.core.netdev_max_backlog = 4096
net.core.somaxconn = 4096

net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_tw_recycle = 0
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.ip_local_port_range = 10000 65000
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_max_tw_buckets = 5000
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_congestion_control = hybla</pre>

**经测试，设置以后ss速度反而有所下降，但是vpn速度提升。。。不知道是不是这几天网络问题。。回头再看看**