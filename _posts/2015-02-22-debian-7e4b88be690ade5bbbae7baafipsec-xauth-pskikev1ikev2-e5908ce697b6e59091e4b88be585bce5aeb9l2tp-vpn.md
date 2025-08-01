---
id: 151
title: Debian 7 下搭建纯IPSEC XAUTH PSK/IKEv1/IKEv2 同时向下兼容L2TP VPN
date: 2015-02-22T22:58:59+00:00
author: coffeecat
layout: post


categories:


---
由于debian上最终版本的openswan对iOS系统自带的VPN兼容性不好，另外openswan已经被strongswan所替代且debian也宣布不再支持它，加之openswan不支持IKEv2这种高级货，因此打算用strongswan 5.2.2搭一个ipsec服务，搞一个纯IPSEC的VPN，本来想彻底抛弃L2TP的，无奈现有的openwrt/ddwrt路由器均不支持IKEv2（只有少数企业级的路由器例如思科和华为的才支持IKEv2），所以还是保留一下l2tp。  
先说说StrongSwan和IKEv2的优点吧：  
StrongSwan是一个完整的在Linux的 2.6和3.x内核下实现的的IPsec，支持x509等证书和智能卡认证。StrongSwan支持IKEv1并完全实现了IKEv2协议。

**Internet Key Exchange** (**IKEv1** or **IKEv2**)<span class="goog-text-highlight">是一个用于建立安全协作的IPSEC</span><span class="goog-text-highlight">协议套件</span>,**IKEv2**支持多并发，集群化，并被工业化VPN网关所支持，是被广大跨国企业采纳的VPN方案（路由器支持）。IKEv2在v1的基础上增强了抗中间人攻击（并不是完全防止）、DDOS攻击，重放攻击等特性，并可以支持多种方法对称的认证，我的理解是：皆可以选择用证书认证，或者一方用证书，一方用共享密钥，甚至双方使用共享密钥。  
由于IKEv2是基于UDP协议的，所以它具有天然的对移动性（MOBIKE）的支持，更能适应不断变化的、不稳定的网络连接，甚至可以在有线和无线连接之间无缝切换。所以特别适合移动设备使用。  
由于PPTP确认可以被NSA破解，L2TP/IPSEC标准也有被NSA削弱的迹象，而OPEN-VPN和SSTP使用具有很大局限性（参考文档4），因此我认为IKEv2是目前最好的VPN解决方案（最安全的广泛认为仍然是OPEN-VPN，需搭配合适的加密算法）。

下面是安装流程：

# 1.卸载openswan，删除/etc/init.d/ipsec，卸载ipsec service

<pre class="lang:sh decode:true ">apt-get remove openswan
service ipsec stop
update-rc.d -f ipsec remove
rm /etc/init.d/ipsec</pre>

# 2.下载编译安装strongswan

<!--more-->

<pre class="lang:sh decode:true ">apt-get update
apt-get install build-essential     #编译环境
aptitude install libgmp3-dev libssl-dev pkg-config libpcsclite-dev libpam0g-dev     #编译所需要的软件
mkdir tmp
cd tmp
wget http://download.strongswan.org/strongswan.tar.gz
tar zxvf strongswan.tar.gz
cd strongswan-5.2.2
./configure --prefix=/usr --sysconfdir=/etc --enable-cisco-quirks --enable-openssl --enable-nat-transport --disable-mysql --disable-ldap --disable-static --enable-shared --enable-md4 --enable-eap-mschapv2 --enable-eap-aka --enable-eap-aka-3gpp2 --enable-eap-gtc --enable-eap-identity --enable-eap-md5 --enable-eap-peap --enable-eap-radius --enable-eap-sim --enable-eap-sim-file --enable-eap-sim-pcsc --enable-eap-simaka-pseudonym --enable-eap-simaka-reauth --enable-eap-simaka-sql --enable-eap-tls --enable-eap-tnc --enable-eap-ttls
apt-get install sysv-rc-conf</pre>

然后编译安装，时间会比较长。。

<pre class="lang:sh decode:true ">make
make install</pre>

# 3.编辑ipsec配置文件ipsec.conf和ipsec.secrets和strongswan.conf

### a.先看看大牛解释的各os对IKE的支持情况吧（参考文档1）：

**linux：** 借助strongswan完整支持ikev1和ikev2。  
**ios 6+：** 仅支持ikev1，且支持得有bug，例如无法从一个3级证书（同时包含客户端、服务器端、CA端证书的证书）里面读取CA证书。。所以需要2个证书。。。而且优先使用不加密的积极模式，还好strongswan不支持积极模式。另外ios 6还有fragmentation bug导致只能使用小于1024位的证书，而且Mac OS X 10.7以后也不支持小证书了，真是一塌糊涂。。。。苹果的staff是这么回答的：

_**ios 6 has a bad bug in udp packet fragmentation handling. Large UDP packets will cause IPSec connections to fail. We&#8217;re fighting through this as well and the only solution we found was to lower the size of the root and device certificates, far less than ideal.**_

**android：** 仅支持ikev1，其他和linux一样，4.x以后可以用strongswan client实现ikev2支持。  
**windows xp**和**vista**完全不支持ikev2，**win7**和**2008v2**开始支持，但是DH协商密钥仅支持mod 1024，导致安全性大大降低。而且有rekey的bug，只好把rekey关闭。

### b.修改ipsec.conf

注意：每个参数前面都是tab，不是空格，否则会报错，这也是开源软件的bug么。。。

<pre class="lang:sh decode:true ">vi /etc/ipsec.conf</pre>

<pre class="lang:vim decode:true ">config setup
	uniqueids=never 
	#上面这个表示允许一个id多个登陆
conn iOS_cert
	keyexchange=ikev1
	# strongswan version &gt;= 5.0.2, compatible with iOS 6.0,6.0.1
	fragmentation=yes
	left=%defaultroute
	leftauth=pubkey
	leftsubnet=0.0.0.0/0
	leftcert=server.cert.pem
	right=%any
	rightauth=pubkey
	rightauth2=xauth
	rightsourceip=10.1.2.0/24
	rightcert=client.cert.pem
	auto=add

# also supports iOS PSK and Shrew on Windows
conn android_xauth_psk
	keyexchange=ikev1
	left=%defaultroute
	leftauth=psk
	leftsubnet=0.0.0.0/0
	right=%any
	rightauth=psk
	rightauth2=xauth
	rightsourceip=10.1.2.0/24
	auto=add

# compatible with "strongSwan VPN Client" for Android 4.0+
# and Windows 7 cert mode.
conn networkmanager-strongswan
	keyexchange=ikev2
	left=%defaultroute
	leftauth=pubkey
	leftsubnet=0.0.0.0/0
	leftcert=server.cert.pem
	right=%any
	rightauth=pubkey
	rightsourceip=10.1.2.0/24
	rightcert=client.cert.pem
	auto=add

#Windows 7 cert+eap-mschapv2 mode. Not Completely Safe.
conn windows7
	keyexchange=ikev2
	ike=aes256-sha1-modp1024! 
	rekey=no
	left=%defaultroute
	leftauth=pubkey
	leftsubnet=0.0.0.0/0
	leftcert=server.cert.pem   #多个证书用逗号隔开
	right=%any
	rightauth=eap-mschapv2
	rightsourceip=10.1.2.0/24
	rightsendcert=never
	eap_identity=%any
	auto=add

#compatible with xl2tp	
conn L2TP-PSK-NAT
	rightsubnet=vhost:%priv
	also=L2TP-PSK-noNAT
 
conn L2TP-PSK-noNAT
	authby=secret
	#pfs=no
	auto=add
	keyingtries=3
	rekey=no
	ikelifetime=8h
	keylife=1h
	type=transport
	left=%defaultroute
	leftprotoport=17/1701
	right=%any
	rightprotoport=17/%any
	dpddelay=40
	dpdtimeout=130
	dpdaction=clear</pre>

### c.修改ipsec.secrets

<pre class="lang:sh decode:true ">vi /etc/ipsec.secrets</pre>

<pre class="lang:vim decode:true ">#
# ipsec.secrets
#
# This file holds the RSA private keys or the PSK preshared secrets for
# the IKE/IPsec authentication. See the ipsec.secrets(5) manual page.
#
: RSA server.pem
: PSK "PSK password"
用户名 : XAUTH "user password"
用户名 : EAP "user password"</pre>

### d.修改strongswan.conf

<pre class="lang:sh decode:true">vi /etc/strongswan.conf</pre>

<pre class="lang:vim decode:true "># strongswan.conf - strongSwan configuration file
charon {
       duplicheck.enable = no

       dns1 = 8.8.8.8
       dns2 = 208.67.220.220

       # for Windows only
       nbns1 = 8.8.8.8
       nbns2 = 208.67.220.220

       filelog {
               /var/log/strongswan.charon.log {
                   time_format = %b %e %T
                   default = 2
                   append = no
                   flush_line = yes
               }
       }
      
       #保留文件原来内容
       ...
}</pre>

# 4.签发证书

### a.生成CA私钥和自签名证书，默认都是RSA 2048：

<pre class="lang:sh decode:true ">ipsec pki --gen --outform pem &gt; ca.pem
ipsec pki --self --in ca.pem --dn "C=info, O=example, CN=example.com CA" --ca --outform pem &gt;ca.cert.pem</pre>

### b.生成服务器私钥，用CA私钥签发服务器证书:

<pre class="lang:sh decode:true ">ipsec pki --gen --outform pem &gt; server.pem
ipsec pki --pub --in server.pem | ipsec pki --issue --cacert ca.cert.pem \
--cakey ca.pem --dn "C=info, O=example, CN=example.com" \
--san="example.com" --flag serverAuth --flag ikeIntermediate \
--outform pem &gt; server.cert.pem</pre>

&#8211;issue, &#8211;cacert 和 &#8211;cakey 就是表明要用刚才自签的 CA 证书来签这个服务器证书。

&#8211;dn, &#8211;san，&#8211;flag 是一些客户端方面的特殊要求：

iOS 客户端要求 CN 也就是通用名必须是你的服务器的 URL 或 IP 地址;  
Windows 7 不但要求了上面，还要求必须显式说明这个服务器证书的用途（用于与服务器进行认证），&#8211;flag serverAuth;  
非 iOS 的 Mac OS X 要求了“IP 安全网络密钥互换居间（IP Security IKE Intermediate）”这种增强型密钥用法（EKU），&#8211;flag ikdeIntermediate;  
Android 和 iOS 都要求服务器别名（serverAltName）就是服务器的 URL 或 IP 地址，&#8211;san。

### c.生成客户端私钥,用CA私钥签发客户证书，并生成移动客户端上使用的p12证书，多个客户端可以使用多个证书，也可以共用一个。这里需要输入2遍证书提取密码，以后安装要用:

<pre class="lang:sh decode:true ">ipsec pki --gen --outform pem &gt; client.pem
ipsec pki --pub --in client.pem | ipsec pki --issue --cacert ca.cert.pem --cakey ca.pem --dn "C=info, O=example, CN=example.com Client" --outform pem &gt; client.cert.pem
openssl pkcs12 -export -inkey client.pem -in client.cert.pem -name "client" -certfile ca.cert.pem -caname "example.com CA"  -out client.cert.p12
</pre>

### d.写一个发证书的脚本，以后省事：

<pre class="lang:sh decode:true ">mkdir CAKEY
cp ./tmp/ca* ./CAKEY/	
vi keymake.sh</pre>

<pre class="lang:vim decode:true ">#!/bin/bash
   read -p "Please input username:" user
   if [ "$user" = "" ]; then
	echo "Error! - you must input an username"
	echo "Exit!"
	exit 1
   fi
   echo "==========================="
   echo "Making ${user}Key.pem ..."
ipsec pki --gen --outform pem &gt; ${user}Key.pem
   echo "Making ${user}Cert.pem ..."
ipsec pki --pub --in ${user}Key.pem | ipsec pki --issue --cacert ./CAKEY/ca.cert.pem --cakey ./CAKEY/ca.pem --dn "C=info, O=example, CN=example.com Client" --outform pem &gt; ${user}Cert.pem
   echo "Making ${user}Cert.p12 ..."
openssl pkcs12 -export -inkey ${user}Key.pem -in ${user}Cert.pem -name ${user} -certfile ./CAKEY/ca.cert.pem -caname "example.com CA" -out ${user}Cert.p12
   echo "========== done =========="</pre>

如要使得新证书生效，需将cert.pem拷贝到/etc/ipsec.d/certs，可能需要重启ipsec服务

<pre class="lang:sh decode:true ">chmod 755 keymake.sh</pre>

### e.拷贝安装证书至服务器，添加防火墙规则，添加自启动服务:

<pre class="lang:sh decode:true ">cp -r ca.cert.pem /etc/ipsec.d/cacerts/
cp -r server.cert.pem /etc/ipsec.d/certs/
cp -r server.pem /etc/ipsec.d/private/
cp -r client.cert.pem /etc/ipsec.d/certs/
cp -r client.pem  /etc/ipsec.d/private/
</pre>

CA 证书、客户证书（两个）和 .p12 证书复制出来给客户端用。有几种 Android 配置还需要服务器证书（server.cert.pem）。

<pre class="lang:sh decode:true ">iptables -A INPUT -p udp --dport 500 -j ACCEPT
iptables -A INPUT -p udp --dport 4500 -j ACCEPT
iptables --table nat --append POSTROUTING --jump MASQUERADE
echo 1 &gt; /proc/sys/net/ipv4/ip_forward</pre>

<pre class="lang:sh decode:true ">vi /etc/rc.local</pre>

在exit0前面加上：

<pre class="lang:sh decode:true ">ipsec start</pre>

重启服务器。

# 4.各平台使用攻略（来自参考文档1，略修改）

### a.iOS

把 CA 证书和之前做好的 pkcs12（.p12）发邮件给自己。在 iOS 上收邮件，导入两者。然后新建 IPSec VPN：

_服务器_，和 openSUSE 的要求一样，都是 IP 或都是 URL  
_账户和密码，_写 ipsec.secrets 里 XAUTH 前后的那两个  
如果要使用证书，证书选刚才的那个。否则可以不使用证书，输入 ipsec.secrets 里设置的 PSK 密码。

### b.Android

**1）自带的VPN功能**

选IPSec Xauth PSK

我的4.4.2是有这个的，设置 VPN 之前 要求你必须设置锁屏密码或者 PIN 码。

主要还是：

_服务器_，同上  
_IPSec 预共享密钥_：写 ipsec.secrets 里 PSK 后面的那个密码。  
然后登入时还是用 XAUTH 前后的那两个做用户名密码。

**2）用&#8221;StrongSwan VPN Client&#8221; for Android 4.0 (ICS)+**

这是官方自己出的客户端，Google Play 里就有。

把之前做好的 pkcs12 发邮件给自己。实际上 pkcs12 里就包含了 CA 证书，iOS 是有 bug 才必须明确要求导入 CA 证书（鄙视之）。Android 不用。直接在 GMail 里点击就会提示你导入。

然后打开官方客户端，新建方案：

_Gateway_ 就是服务器，同上  
_Type_ 选 IKEv2 Certificate  
_User certificate_ 选你刚才导入的  
取消自动选择 CA 证书，然后在用户证书里选你刚才从 pk12 导入的

### c.Windows XP/Vista

注意 XP/Vista 本身不支持纯 IPsec 连接。如果使用 L2TP/IPsec 模式，使用证书会 fallback 到 iOS_cert 这个连接类型，使用预共享密码会 fallback 到 android-xauth-psk 这个连接类型。  
**1）****使用 Shrew Soft VPN Client,_只有十多天试用期。。。_**

下载：https://www.shrew.net/download/vpn

安装后打开，选“Add”：

“General”选项卡下，把“Host Name or IP address”添好  
“Authorization”选项卡下：  
“Authorization Method”选“Mutual PSK + XAuth”  
“Local Identity”的“Identification Type”选“IP Address”  
“Credentials”下面“Pre Shared Key”里输入 PSK 密码  
“Phrase 1”，“Exchange Type”选“Main”  
“Phrase 2”，“PFS Exchange”选“auto”  
保存。连接时用户名密码是你的 XAUTH 用户名密码。

服务器端对应的配置是 android-xauth-psk 的连接类型。

### d.Windows 7+

**1）使用 Shrew Soft VPN Client 客户端：和上面 XP 的一样。**

**2）使用自带客户端（Agile）：**

导入证书：

开始菜单搜索“cmd”，打开后输入 mmc（Microsoft 管理控制台）。  
“文件”-“添加/删除管理单元”，添加“证书”单元  
证书单元的弹出窗口中一定要选“计算机账户”，之后选“本地计算机”，确定。  
在左边的“控制台根节点”下选择“证书”-“个人”，然后选右边的“更多操作”-“所有任务”-“导入”打开证书导入窗口。  
选择刚才生成的 client.cert.p12 文件。下一步输入私钥密码。下一步“证书存储”选“个人”。  
导入成功后，把导入的 CA 证书剪切到“受信任的根证书颁发机构”的证书文件夹里面。  
打开剩下的那个私人证书，看一下有没有显示“您有一个与该证书对应的私钥”，以及“证书路径”下面是不是显示“该证书没有问题”。  
然后关闭 mmc，提示“将控制台设置存入控制台1吗”，选“否”即可。  
至此，证书导入完成。

注意 千万不要双击 .p12 证书导入！因为那样会导入到当前用户而不是本机计算机中，ipsec 守护精灵是访问不了它的。  
建立连接：

“控制面板”-“网络和共享中心”-“设置新的连接或网络”-“连接到工作区”-“使用我的 Internet 连接”  
Internet 地址写服务器地址，注意事项同 openSUSE 的，都是 IP 或都是 URL。  
描述随便写。  
用户名密码写之前配置的 EAP 的那个。  
确定  
点击右下角网络图标，在新建的 VPN 连接上右键属性然后切换到“安全”选项卡。  
VPN 类型选 IKEv2  
数据加密是“需要加密”  
身份认证这里需要说一下，如果想要使用 EAP-MSCHAPV2 的话就选择“使用可扩展的身份认证协议”-“Microsoft 安全密码”，想要使用私人证书认证的话就选择“使用计算机证书”。

本文参考：  
1.https://zh.opensuse.org/SDB:Setup\_Ipsec\_VPN\_with\_Strongswan  
2.http://blog.ltns.info/linux/pure\_ipsec\_multi-platform\_vpn\_client\_debian\_vps/  
3.http://www.nsshell.com/archives/285  
4.https://www.bestvpn.com/blog/4147/pptp-vs-l2tp-vs-openvpn-vs-sstp-vs-ikev2/