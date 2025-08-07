---
id: 460
title: 解决Openwrt Readonly file system文件系统只读的问题
date: 2015-11-30 21:29:59+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
由于Openwrt关闭不好的问题，重启进入openwrt，发现luci 配置无法写入，进入ssh发现remounting file system is read only&#8230;但是又不想重装。。。由于这是根文件系统已挂载，所以e2fs无法在该系统里面修复文件系统错误。  
于是机智的我在esxi里面又开了个openwrt虚拟机，其实用linux发行版也行啦，挂载上述出问题的openwrt的盘，但不要mount，进入系统后，因为出问题的盘是sdb的sdb2,运行：

```sh
e2fsck /dev/sdb2
```

```vim
e2fsck 1.42.12 (29-Aug-2014)
/dev/sdb2 was not cleanly unmounted, check forced.
Pass 1: Checking inodes, blocks, and sizes
Pass 2: Checking directory structure
Pass 3: Checking directory connectivity
Pass 4: Checking reference counts
Pass 5: Checking group summary information
Block bitmap differences:  +(368--376)
Fix<y>? yes
Free blocks count wrong for group #0 (2660, counted=2651).
Fix<y>? yes
Free blocks count wrong for group #1 (1807, counted=1803).
Fix<y>? yes
Free blocks count wrong (764951, counted=764938).
Fix<y>? yes
yyy
/dev/sdb2: ***** FILE SYSTEM WAS MODIFIED *****
/dev/sdb2: 2061/385024 files (0.0% non-contiguous), 21494/786432 blocks
```

修复成功后，关闭该虚拟机，然后移除盘，重启原来坏掉的openwrt虚拟机，当当当，成功了~~