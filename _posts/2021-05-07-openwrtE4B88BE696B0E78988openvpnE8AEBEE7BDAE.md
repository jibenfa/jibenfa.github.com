---
id: 780
title: openwrt下新版openvpn设置
date: 2021-05-07T22:39:31+00:00
author: coffeecat
layout: post


categories:


---
最近更新了openvpn版本，一些命令和设置跟以前不一样了。记录一下
1.生成证书
1）编辑/etc/easy-rsa/vars，修改部分内容

<pre class="lang:vim decode:true " ># Choose a size in bits for your keypairs. The recommended value is 2048.  Using
# 2048-bit keys is considered more than sufficient for many years into the
# future. Larger keysizes will slow down TLS negotiation and make key/DH param
# generation take much longer. Values up to 4096 should be accepted by most
# software. Only used when the crypto alg is rsa (see below.)

set_var EASYRSA_KEY_SIZE	4096

# In how many days should the root CA key expire?

set_var EASYRSA_CA_EXPIRE	3650

# In how many days should certificates expire?

set_var EASYRSA_CERT_EXPIRE	3650

# These are the default values for fields
# which will be placed in the certificate.
# Don't leave any of these fields blank.
export KEY_COUNTRY="xx"
export KEY_PROVINCE="xx"
export KEY_CITY="xxxx"
export KEY_ORG="XXxxxx"
export KEY_EMAIL="xxxxxx@gmail.com"
export KEY_OU="XXxxxxxx"
</pre>

2）接着生成证书和diffie-hellman key：  
手工清空/etc/easy-rsa/下的key目录或者运行：
<pre class="lang:vim decode:true " >
easyrsa clean-all  
easyrsa init-pki
</pre>
生成ca证书
<pre class="lang:vim decode:true " >
easyrsa build-ca nopass 
</pre>
生成dh密钥 
<pre class="lang:vim decode:true " >
easyrsa gen-dh  
</pre>
服务器证书
<pre class="lang:vim decode:true " >
easyrsa build-server-full server nopass
</pre>
客户端证书给coffeecat
<pre class="lang:vim decode:true " >
easyrsa build-client-full coffeecat nopass
</pre>
生成ta.key
<pre class="lang:vim decode:true " >
openvpn --genkey --secret ta.key
</pre>

拷贝到服务器目录下：

<pre class="lang:sh decode:true " >cd /etc/easy-rsa/keys/
cp ca.crt ca.key dh4096.pem server.key server.crt /etc/openvpn/</pre>

拷贝到客户端：  
ca.crt dh4096.pem coffeecat.key coffeecat.crt

然后就是最关键的配置openvpn服务器端和客户端了：  
路由器服务器端：  
编辑/etc/config/openvpn :

_注意：172.24.1.1为路由器的lan ip，172.24.1.100-172.24.1.105是为vpn客户端分配的ip端，一定要和路由器为lan dhcp的ip段错开。_

<pre class="lang:vim decode:true " >config openvpn 'tap_cert'
	option port '1194'
	option proto 'tcp4'
	option dev 'tap0'
	option ca '/etc/openvpn/ca.crt'
	option cert '/etc/openvpn/server.crt'
	option key '/etc/openvpn/server.key'
	option dh '/etc/openvpn/dh4096.pem'
	option tls_auth '/etc/openvpn/ta.key 0'
	option server_bridge '172.24.1.2 255.255.255.0 172.24.1.32 172.24.1.63'
	option ifconfig_pool_persist '/tmp/ipp.txt'
	option duplicate_cn '1'
	option client_to_client '1'
	option keepalive '10 120'
	option compress 'lzo'
	option status '/tmp/openvpn-status.log'
	list push 'redirect-gateway def1 local'
	option verb '3'
	option enabled '1'

config openvpn 'tun_cert'
	option port '3366'
	option proto 'tcp4'
	option dev 'tun0'
	option ca '/etc/openvpn/ca.crt'
	option cert '/etc/openvpn/server.crt'
	option key '/etc/openvpn/server.key'
	option dh '/etc/openvpn/dh4096.pem'
  option tls_auth '/etc/openvpn/ta.key 0'
	option server '10.1.1.0 255.255.255.0'
	option client_config_dir '/etc/openvpn/tunstatic'
	option ccd_exclusive '1'
	option cipher 'AES-256-CBC'
	option ifconfig_pool_persist '/tmp/ipp2.txt'
	option duplicate_cn '1'
	option client_to_client '1'
	option keepalive '10 120'
	option compress 'lzo'
	option persist_key '1'
	option persist_tun '1'
	option status '/tmp/openvpn-status2.log'
	option verb '3'
	option topology 'subnet'
	list push 'dhcp-option DNS 172.24.1.1'
	list push 'redirect-gateway def1 local'
	option enabled '1'

config openvpn 'tun_router'
	option port '3377'
	option proto 'tcp4'
	option dev 'tun1'
	option ca '/etc/openvpn/ca.crt'
	option cert '/etc/openvpn/server.crt'
	option key '/etc/openvpn/server.key'
	option dh '/etc/openvpn/dh4096.pem'
	option tls_auth '/etc/openvpn/ta.key 0'
	option server '10.0.1.0 255.255.255.0'
	option client_config_dir '/etc/openvpn/ccd'
	option ccd_exclusive '1'
	option ifconfig_pool_persist '/tmp/ipp3.txt'
	option client_to_client '1'
	option keepalive '10 120'
	option compress 'lzo'
	option persist_key '1'
	option persist_tun '1'
	option status '/tmp/openvpn-status3.log'
	option verb '3'
	option topology 'subnet'
	list push 'route 172.24.1.0 255.255.255.0'
	list route '172.24.8.0 255.255.255.0'
	option enabled '1'

</pre>

然后在luci或者命令行启动openvpn：

<pre class="lang:sh decode:true " >/etc/init.d/openvpn start</pre>

ps一下有进程就对了

windows7 openvpn客户端配置：  
C:\Program Files\OpenVPN\config\client.ovpn

<pre class="lang:vim decode:true " >client

dev tap
proto tcp

remote xxxxxxxxxxxxx 1194 #路由器的ddns地址或者IP 端口
resolv-retry infinite
nobind

persist-tun
persist-key

float
ca ca.crt
cert coffeecat.crt
key coffeecat.key
mute-replay-warnings
comp-lzo
verb 4
##下面两行for WIN7
route-method exe
route-delay 2</pre>

最后在路由器上增加自定义iptables规则：  
先把tap0放到lan区域中，然后在自定义规则里面加上：

<pre class="lang:sh decode:true " >iptables -I INPUT 1 -p tcp --dport 1194 -j ACCEPT
iptables -I INPUT 1 -p udp --dport 1194 -j ACCEPT</pre>

另外win7里面要设置一下metric，否则可能不是走的vpn这个路，设完以后，可以看到vpn的跃点最小：

<pre class="lang:vim decode:true " >IPv4 路由表
===========================================================================
活动路由:
网络目标        网络掩码          网关       接口   跃点数
          0.0.0.0          0.0.0.0       172.24.1.1     172.24.1.100     50
          0.0.0.0          0.0.0.0       172.24.0.1     172.24.0.150    281</pre>

参考：

1.https://excited.tech/2015/07/05/e588a9e794a8openvpne8bf9ce7a88be8bf9ee59b9ee5aeb6e9878ce8b7afe794b1e599a8e4b88ae58685e5a496e7bd91e38082e38082e38082.html
