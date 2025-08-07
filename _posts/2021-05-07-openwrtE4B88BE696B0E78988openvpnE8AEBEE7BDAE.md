---
id: 780
title: openwrt下新版openvpn设置
date: 2021-05-07 22:39:31+00:00
author: coffeecat
layout: post
categories:
- openwrt
- 科学上网
tags:
- openwrt
- 科学上网
---
最近更新了openvpn版本，一些命令和设置跟以前不一样了。现记录一下：

1.生成证书

1）编辑/etc/easy-rsa/vars，修改部分内容

```vim
# Choose a size in bits for your keypairs. The recommended value is 2048.  Using
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

```

2）接着生成证书和diffie-hellman key：  
手工清空/etc/easy-rsa/下的key目录或者运行：
```vim

easyrsa clean-all  
easyrsa init-pki

```
生成ca证书
```vim

easyrsa build-ca nopass 

```
生成dh密钥 
```vim

easyrsa gen-dh  

```
服务器证书
```vim

easyrsa build-server-full server nopass

```
客户端证书给coffeecat
```vim

easyrsa build-client-full coffeecat nopass

```
生成ta.key
```vim

openvpn --genkey --secret ta.key

```

3）拷贝到服务器目录下：

```sh
cd /etc/easy-rsa/keys/
cp ca.crt ca.key dh4096.pem server.key server.crt ta.key /etc/openvpn/
```

4）将以下文件拷贝到客户端或者将文件的内容贴在客户端配置文件中（移动设备）：  
ca.crt dh4096.pem coffeecat.key coffeecat.crt ta.key

5）然后就是最关键的配置openvpn服务器端和客户端了：  
路由器服务器端：  
编辑/etc/config/openvpn :

_注意：172.24.1.1为路由器的lan ip，10.1.1.0/24是为vpn客户端分配的ip段，一定要和路由器为lan dhcp的ip段错开。_

```vim


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

```

在/etc/openvpn/tunstatic文件夹下创建名为coffeecat的文件，内容为：

```vim

ifconfig-push 10.1.1.7 255.255.255.0

```

然后在luci或者命令行启动openvpn：

```sh
/etc/init.d/openvpn restart
```

ps一下有进程就对了

openvpn客户端配置client.ovpn,此处设置为单文件模式：
```vim

client
dev tun
proto tcp4
connect-retry-max 5
connect-retry 5


remote 你的服务器地址 3366
resolv-retry infinite
nobind
float
persist-key
persist-tun
remote-cert-tls server
comp-lzo
verb 3
cipher		AES-256-CBC
tun-mtu		1500
key-direction 1

<tls-auth>
#
# 2048 bit OpenVPN static key
#
-----BEGIN OpenVPN Static key V1-----
此处省略。。。。。
-----END OpenVPN Static key V1-----
</tls-auth>

<ca>
-----BEGIN CERTIFICATE-----
此处省略。。。。。
-----END CERTIFICATE-----
</ca>

<cert>
-----BEGIN CERTIFICATE-----
此处省略。。。。。
-----END CERTIFICATE-----
</cert>

<key>
-----BEGIN PRIVATE KEY-----
此处省略。。。。。
-----END PRIVATE KEY-----
</key>


```
特别要注意的是，server配置文件中的：
```vim

option tls_auth '/etc/openvpn/ta.key 0'


```
要和client配置文件中的：
```vim

key-direction 1
<tls-auth>
#
# 2048 bit OpenVPN static key
#
-----BEGIN OpenVPN Static key V1-----
此处省略。。。。。
-----END OpenVPN Static key V1-----
</tls-auth>


```
对应，否则无法连通。

