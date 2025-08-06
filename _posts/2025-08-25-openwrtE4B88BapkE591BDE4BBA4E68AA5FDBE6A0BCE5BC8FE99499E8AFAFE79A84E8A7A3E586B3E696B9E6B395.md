---
id: 822
title: openwrt下apk命令报FDB格式错误的解决方法
date: 2025-08-05 04:23:13+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
- apk
---

话说openwrt正式版安装命令是opkg，现在snapshot里面变成了apk。前几天尝试了一下，居然得到一个报错：

<figure class="highlight"><pre><code class="language-r" data-lang="r">
  
root@OpenWrt:~# apk update
ERROR: FDB format error (line 7002, entry 'Z')
ERROR: Unable to read database: v2 database format error
ERROR: Failed to open apk database: v2 database format error

</code></pre></figure>

研究了一下，其实这个报错，跟以前opkg被lock的情况有点相似，只不过是apk采用了数据库，更新的时候异常关闭导致的。

解决方案是：

打开/lib/apk/db 里面有个installed 的数据库，然后找到报错的行，进行修改。当然也可以简单删除这个库，只不过会导致重新安装一遍所有软件，不建议直接删。

话说使用snapshot要慎重，用apk的话以前现成的*.ipk的安装包统统不能用了，要重新编译打包成*.apk包。另外snapshot下缺失不少软件，例如mtk的bind-dig就没有，还有就是稳定性的问题。
