---
id: 28
title: Debian 7 配置L2TP IPSEC 科学上网一键安装脚本
date: 2015-02-09T21:48:57+00:00
author: coffeecat
layout: post




categories:


---
随着功夫墙的不断升级，连code.google.com都上不去了，做开发的愁啊。而且vpn供应商也封得差不多了，还不如自己搭一个，顺便学习一下。  
这时无意在网上看到Linode VPS降到$10了，立马入了一个，真是好用。。。  
Linode 1024 plan包括： E5-2680 v2 @ 2.80GHz 1 Core，1 G Ram，24 G SSD，每月2TB流量，125Mbit outbound的带宽，真是太划算了。

我的referral code： **494568e6b3eef8bbd177cbb548dc952f6718739c** ，要是大伙买的时候写一下我的code那是感激不尽拉。。。  
Linode非常人性化，装个系统直接可以在网站界面上装，各种打好补丁的Linux系统分分钟就装好了。。。  
远程putty连上，就可以开工了。

系统使用Debian7，  
L2TP使用xl2tpd,  
IPSEC使用openswan，  
注：openswan已经不在debian支持了，debian建议使用strongswan，但是人家[DHQ攻略](http://dhq.me/one-key-deploy-ipsec-l2tp-vpn-on-debian-centos)是openswan，所以我也就直接拿来用了，改动了不少脚本。

脚本改动内容：  
1.降低openswan版本，修改了部分xl2tpd脚本，增加了ios支持，经测试ios可以连接，且稳定  
2.增加了iptable防火墙规则和安装fail2ban，防止ssh root密码尝试，不但威胁安全，还浪费流量。  
3.增加ipsec自启动脚本  
4.修改了一些小细节

远程连接后先创建一键脚本

root@xxx:touch xxxx.sh

root@xxx:chmod +x xxxx.sh

root@xxx:vi xxxx.sh

里面填以下内容，前20行内容按照实际修改  
<!--more-->

<pre lang="bash" line="0" file="download.txt" colla="+">#!/bin/sh
 
 
#VPN 账号
vpn_name="username"
 
#VPN 密码
vpn_password="password"
 
#设置 PSK 预共享密钥
psk_password="123456"
 
#公网IP
ip="yourip"
 
 
#安装 openswan、xl2tpd(有弹对话框的话直接按回车就行)
apt-get install -y xl2tpd screen

#apt-get的默认版本的openswan对于ios支持有问题，为了支持ios，只好降版本，
#这个版本的Opportunistic Encryption Support不要打开，否则会有安全漏洞
#debian已经不再对openswan支持了，以后都是strongswan了。。。
apt-get install openswan=1:2.6.37-3 
#apt-get install -y openswan xl2tpd screen


 
#备份 /etc/ipsec.conf 文件,注意参数前面都是tab不是空格,拍空格会出错
ipsec_conf="/etc/ipsec.conf"
if [ -f $ipsec_conf ]; then
cp $ipsec_conf $ipsec_conf.bak
fi
echo "
version 2.0
config setup
	nat_traversal=yes
	virtual_private=%v4:10.0.0.0/8,%v4:192.168.0.0/16,%v4:172.16.0.0/12
	oe=off
	protostack=netkey
 
conn L2TP-PSK-NAT
	rightsubnet=vhost:%priv
	also=L2TP-PSK-noNAT
 
conn L2TP-PSK-noNAT
	authby=secret
	pfs=no
	auto=add
	keyingtries=3
	rekey=no
	ikelifetime=8h
	keylife=1h
	type=transport
	left=$ip
	leftprotoport=17/1701
	right=%any
	rightprotoport=17/%any
	dpddelay=40
	dpdtimeout=130
	dpdaction=clear
" > $ipsec_conf
 
 
 
#备份 /etc/ipsec.secrets 文件
ipsec_secrets="/etc/ipsec.secrets"
if [ -f $ipsec_secrets ]; then
cp $ipsec_secrets $ipsec_secrets.bak
fi
echo "
$ip   %any:  PSK \"$psk_password\"
" >> $ipsec_secrets
 
 
 
#备份 /etc/sysctl.conf 文件
sysctl_conf="/etc/sysctl.conf"
if [ -f $sysctl_conf ]; then
cp $sysctl_conf $sysctl_conf.bak
fi
echo "
net.ipv4.ip_forward = 1
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
" >> $sysctl_conf
sysctl -p
 
for each in /proc/sys/net/ipv4/conf/*
do
echo 0 > $each/accept_redirects
echo 0 > $each/send_redirects
done
 
 
#设置 l2tp
xl2tpd="/etc/xl2tpd/xl2tpd.conf"
if [ -f $xl2tpd ]; then
cp $xl2tpd $xl2tpd.bak
fi
echo "
[global]
ipsec saref = no
 
[lns default]
ip range = 10.1.2.2-10.1.2.255
local ip = 10.1.2.1
refuse chap = yes
refuse pap = yes
require authentication = yes
ppp debug = yes
pppoptfile = /etc/ppp/options.xl2tpd
length bit = yes
" > $xl2tpd
 
 
#设置 ppp,最后三项是为了兼容ios
#mtu 1400 #解决ios打不开网页的问题
#noccp #解决ios连接问题
#connect-delay 5000 #解决ios连接超时问题
options_xl2tpd="/etc/ppp/options.xl2tpd"
if [ -f $options_xl2tpd ]; then
cp $options_xl2tpd $options_xl2tpd.bak
fi
echo "
require-mschap-v2
ms-dns 8.8.8.8
ms-dns 8.8.4.4
asyncmap 0
auth
crtscts
lock
hide-password
modem
debug
name l2tpd
proxyarp
lcp-echo-interval 30
lcp-echo-failure 4
mtu 1400
noccp
connect-delay 5000
" > $options_xl2tpd
 
#添加 VPN 账号
chap_secrets="/etc/ppp/chap-secrets"
if [ -f $chap_secrets ]; then
cp $chap_secrets $chap_secrets.bak
fi
echo "
$vpn_name * $vpn_password *

" >> $chap_secrets
 
 
#设置 iptables 的数据包转发
iptables --table nat --append POSTROUTING --jump MASQUERADE
echo 1 > /proc/sys/net/ipv4/ip_forward
#如果要封某个网段：
iptables -I INPUT -s 103.41.124.0/24 -j DROP
#处理IP碎片数量,防止攻击,允许每秒100个
iptables -A FORWARD -f -m limit --limit 100/s --limit-burst 100 -j ACCEPT
#设置ICMP包过滤,允许每秒1个包,限制触发条件是10个包
iptables -A FORWARD -p icmp -m limit --limit 1/s --limit-burst 10 -j ACCEPT

#安装fail2ban，默认限制ssh登陆失败6次封10分钟
#可以通过/etc/fail2ban/jail.conf来改变
apt-get install fail2ban 
update-rc.d fail2ban defaults

#保存iptables:
iptables-save > /etc/network/iptables


iptables_sh="/etc/init.d/iptables.sh"
if [ -f $iptables_sh ]; then
cp $iptables_sh $iptables_sh.bak
fi
touch $iptables_sh
chmod +x $iptables_sh
echo "
#!/bin/sh
### BEGIN INIT INFO
# Provides:          iptables.sh
# Required-Start:    $local_fs $remote_fs $network $syslog
# Required-Stop:     $local_fs $remote_fs $network $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: update iptables
# Description:       update iptalbes
### END INIT INFO
/sbin/iptables-restore &lt; /etc/network/iptables 
" > $iptables_sh
update-rc.d iptables.sh defaults
 
/etc/init.d/ipsec stop
 
/etc/init.d/xl2tpd stop
 
/etc/init.d/ipsec start
 
screen -dmS xl2tpd xl2tpd -D
 
ipsec verify
 
echo "###########################################"
echo "##L2TP VPN SETUP COMPLETE!"
echo "##VPN IP  :   $ip"
echo "##VPN USER:   $vpn_name"
echo "##VPN PASSWORD:   $vpn_password"
echo "##VPN PSK :   $psk_password"
echo "###########################################"


##################################################
#如果Pluto listening for IKE on udp 500 
apt-get install lsof
##################################################

#vpn自启动
update-rc.d ipsec defaults


</pre>

开始运行  
root@xxx:sh ./xxxx.sh

如果结果如下，则ok：

<pre class="lang:sh decode:true " >Checking your system to see if IPsec got installed and started correctly:
Version check and ipsec on-path [OK]
Linux Openswan xxx (netkey)
Checking for IPsec support in kernel [OK]
SAref kernel support [N/A]
NETKEY: Testing XFRM related proc values [OK]
[OK]
[OK]
Checking that pluto is running [OK]
Pluto listening for IKE on udp 500 [OK]
Pluto listening for NAT-T on udp 4500 [OK]
Two or more interfaces found, checking IP forwarding [OK]
Checking NAT and MASQUERADEing [OK]
Checking for 'ip' command [OK]
Checking /bin/sh is not /bin/dash [WARNING]
Checking for 'iptables' command [OK]
Opportunistic Encryption Support [DISABLED]</pre>

大工搞成，用PC或者手机连连试试吧~~

鸣谢 http://dhq.me/one-key-deploy-ipsec-l2tp-vpn-on-debian-centos