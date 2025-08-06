---
id: 434
title: Openwrt 格式化4T 单个分区硬盘(GPT)
date: 2015-07-28 18:13:54+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
首先保证硬盘所有分区已经删除，即整个硬盘处于初始化状态。  
ssh进入openwrt：

<pre><code class="language-sh">opkg update
opkg install tune2fs e2fsprog  
mkfs.ext4  /dev/sdb
tune2fs -i 0 -c 0 -r 0 -m 0 /dev/sdb</code></pre>

tune2fs我编译op的时候木有编译进去，但是我从op官网下了个bb x86版本的，居然好用。。。

使用tune2fs之前，mkfs.ext4默认  
(5.00%) reserved for the super user  
即保留了5%给超级用户，浪费了我200GB的空间，不可忍啊。。。

<pre><code class="language-vim">Filesystem           1M-blocks      Used Available Use% Mounted on
rootfs                  135474        34    135424   0% /
/dev/root               135474        34    135424   0% /
tmpfs                     1421         1      1420   0% /tmp
tmpfs                        1         0         1   0% /dev
/dev/sda3               103706       333     98083   0% /mnt/sda3
/dev/sdb               3755449        68   3564592   0% /mnt/nasdisk0</code></pre>

运行了tune2fs以后，找回来了。。。。

<pre><code class="language-vim">Filesystem           1M-blocks      Used Available Use% Mounted on
rootfs                  135474        34    135423   0% /
/dev/root               135474        34    135423   0% /
tmpfs                     1421         1      1420   0% /tmp
tmpfs                        1         0         1   0% /dev
/dev/sda3               103706       333     98083   0% /mnt/sda3
/dev/sdb               3755449        68   3755365   0% /mnt/nasdisk0</code></pre>