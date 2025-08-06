---
id: 321
title: 批量下载Openwrt官网packages脚本，搭建自己的软件源
date: 2015-04-29 23:34:09+00:00
author: coffeecat
layout: post
categories:
- openwrt
- 编程
tags:
- openwrt
- 编程
---
由于Openwrt官网的Chaos Calmer的trunk每天更新一次，如果装了某天的包，第二天要装kernel dependent的软件就比较麻烦了，所以一般都要全部下载下来，自己搭个软件源，以下脚本就是提供了批量下载的（需要在linux环境下运行）：

例如在/root/wrt1900ac/packages下：

<pre><code class="language-sh">vi downloadpackages.sh</code></pre>

<pre><code class="language-vim">#!/bin/sh

mkdir /root/wrt1900ac/packages/base
cd /root/wrt1900ac/packages/base
wget  http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/base/
wget -i index.html -F -B http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/base/

mkdir /root/wrt1900ac/packages/luci
cd /root/wrt1900ac/packages/luci
wget  http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/luci/
wget -i index.html -F -B http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/luci/

mkdir /root/wrt1900ac/packages/management
cd /root/wrt1900ac/packages/management
wget  http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/management/
wget -i index.html -F -B http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/management/

mkdir /root/wrt1900ac/packages/packages
cd /root/wrt1900ac/packages/packages
wget  http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/packages/
wget -i index.html -F -B http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/packages/

mkdir /root/wrt1900ac/packages/routing
cd /root/wrt1900ac/packages/routing
wget  http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/routing/
wget -i index.html -F -B http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/routing/

mkdir /root/wrt1900ac/packages/telephony
cd /root/wrt1900ac/packages/telephony
wget http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/telephony/
wget -i index.html -F -B http://downloads.openwrt.org/snapshots/trunk/mvebu/generic/packages/telephony/

</code></pre>

<pre><code class="language-sh">chmod +x downloadpackages.sh</code></pre>