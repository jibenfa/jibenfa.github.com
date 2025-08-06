---
id: 246
title: Openwrt 路由器使用adbyby插件去除网页和视频网站广告
date: 2015-03-21 19:35:14+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
上网打开网页，看视频都会有广告**弹出**，很是烦人。为了避免这个问题，在op的路由器中装上adbyby插件就能去掉“不[可接受的](https://adblockplus.org/zh_CN/acceptable-ads#criteria)”广告。

ssh登陆gl-inet路由器(基于OPENWRT-AR71XX(AR913X)，adbyby官网上下载对应插件)，输入：

<pre><code class="language-sh">mkdir adbyby
cd adbyby
wget http://info.adbyby.com/download/openwrt.tar.gz
tar -xzvf openwrt.tar.gz
cd bin
chmod +x adbyby
vi /etc/rc.local</code></pre>

在exit 0 前加入

<pre><code class="language-vim">/root/adbyby/bin/adbyby&
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8118</code></pre>

另外更新adhook.ini中的exrule：  
vi /root/adbyby/bin/adhook.ini  
找到[exrule]，修改为：

<pre><code class="language-vim">[exrule]^M
rule=https://easylist-downloads.adblockplus.org/easylistchina.txt^M
rule=https://easylist-downloads.adblockplus.org/easyprivacy.txt^M</code></pre>

重启路由器，搞定。。。  
经测试：打开网易、优酷，页面没有讨厌的广告了，也不会弹出广告，视频内嵌的前置广告也没了。。。手机浏览器也是。。。  
但是手机的app内置的广告还是有的，另外某些广告还是存在，大概是属于“[Adblock Plus 认为的可接受的广告](https://adblockplus.org/zh_CN/acceptable-ads#criteria)”吧。。。

由于adbyby不是很稳定，一旦挂掉就不能上网了，所以按照  
http://www.groad.net/bbs/thread-8832-1-1.html （有修改）创建守护进程，一旦adbyby进程挂了，就重启进程。。。

<pre><code class="language-sh">vi /etc/check_ad_by_by.sh</code></pre>

<pre><code class="language-vim">#!/bin/sh
 
mon() {
while [ "1" ];
do
 cc=`ps | grep adbyby | grep -v grep | grep -v catch`
 if [ -z "$cc" ];then
    /root/adbyby/bin/adbyby& &gt;/dev/null
 fi
 sleep 4
done
}
 
mon &</code></pre>

<pre><code class="language-sh">chmod a+x /etc/check_ad_by_by.sh</code></pre>

<pre><code class="language-sh">vi /etc/rc.local</code></pre>

在exit 0前加入

<pre><code class="language-vim">/etc/check_ad_by_by.sh</code></pre>

另外为了防止adbyby 僵死,可以定期检查重启adbyby：

<pre><code class="language-sh">vi /etc/restart_ad_by_by.sh</code></pre>

<pre><code class="language-sh">#!/bin/sh

ping -c 1 www.baidu.com &gt; /dev/null
ret=$?
if [ $ret -eq 0 ]
then
echo ' It seems OK ! '
else
echo ' restarting adbyby! '
killall -9 adbyby
/root/adbyby/bin/adbyby& &gt;/dev/null

fi</code></pre>

<pre><code class="language-sh">chmod a+x /etc/restart_ad_by_by.sh</code></pre>

在crontab里面增加

<pre><code class="language-sh">0 * * * * /etc/restart_ad_by_by.sh</code></pre>

每小时检查重启adbyby

如果adbyby还是无法启动，可能需要安装libstdcpp

<pre><code class="language-sh">opkg install libstdcpp
</code></pre>