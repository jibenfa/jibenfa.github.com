---
id: 622
title: 利用Openwrt路由部署Openvpn进行两地组网
date: 2017-03-07T08:42:43+00:00
author: coffeecat
layout: post


categories:

---
最近实践了一下利用Openwrt路由部署Openvpn进行两地组网，目标是实现两个局域网互相访问。  
配置：  
1.Openvpn服务端（内部局域网段172.24.1.0/24）：  
首先/etc/config/network配置加一个interface：

<pre class="lang:vim decode:true " >config interface 'vpn1'
    option proto 'none'
    option ifname 'tun1'</pre>

/etc/config/openvpn文件增加内容：  
<!--more-->

<pre class="lang:vim decode:true " > 
config openvpn 'tun_router'
        option port '3377'
        option proto 'tcp'
        option dev 'tun1'
        option ca '/etc/openvpn/ca.crt'
        option cert '/etc/openvpn/server.crt'
        option key '/etc/openvpn/server.key'
        option dh '/etc/openvpn/dh2048.pem'
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
        option enabled '1'
        option topology 'subnet'
        list push 'route 172.24.1.0 255.255.255.0'
        list route '172.24.8.0 255.255.255.0'

</pre>

/etc/openvpn/ccd文件夹内增加一个文件，文件名为客户端证书的common name，例如tbjj，内容为：

<pre class="lang:vim decode:true " >ifconfig-push "10.0.1.6 255.255.255.0"
iroute 172.24.8.0 255.255.255.0</pre>

然后在防火墙自定义规则里面添加：

<pre class="lang:sh decode:true " >iptables -I INPUT 1 -p tcp --dport 3377 -j ACCEPT
iptables -I INPUT 1 -p udp --dport 3377 -j ACCEPT
iptables -A FORWARD -i tun1 -s 10.0.1.0/24 -d 172.24.1.0/24 -j ACCEPT
iptables -A FORWARD -i tun1 -s 172.24.8.0/24 -d 172.24.1.0/24 -j ACCEPT
iptables -I INPUT -i tun1 -s 172.24.8.0/24 -j ACCEPT
iptables -A FORWARD -o tun1 -s 172.24.1.0/24 -j ACCEPT</pre>

2.Openvpn客户端（内部局域网段172.24.8.0/24）：  
首先/etc/config/network配置加一个interface：

<pre class="lang:vim decode:true " >config interface 'vpn1'
    option proto 'none'
    option ifname 'tun1'</pre>

/etc/config/openvpn文件增加内容：

<pre class="lang:vim decode:true " >
config openvpn 'vpn_client'
        option client '1'
        option dev 'tun1'
        option proto 'tcp'
        list remote '远端地址 3377'
        option remote_cert_tls 'server'
        option remote_random '1'
        option resolv_retry 'infinite'
        option persist_key '1'
        option persist_tun '1'
        option ca '/etc/openvpn/ca.crt'
        option cert '/etc/openvpn/tbjj.crt'
        option key '/etc/openvpn/tbjj.key'
        option compress 'lzo'
        option verb '3'
        option enabled '1'
        option nobind '1'
        option auth_nocache '1'

        </pre>

然后防火墙自定义规则添加：

<pre class="lang:vim decode:true " >iptables -I INPUT 1 -p tcp --dport 1195 -j ACCEPT
iptables -I INPUT 1 -p udp --dport 1195 -j ACCEPT
iptables -A FORWARD -i tun1 -s 172.24.1.0/24 -d 172.24.8.0/24 -j ACCEPT
iptables -I INPUT -i tun1 -s 172.24.1.0/24 -j ACCEPT
iptables -A FORWARD -i tun1 -s 10.0.1.0/24 -d 172.24.8.0/24 -j ACCEPT
iptables -A FORWARD -o tun1 -s 172.24.8.0/24 -j ACCEPT
 </pre>

3.最后重启两个路由，2个局域网就可以互相访问了。

参考资料：  
1.http://blog.ltns.info/linux/connect\_two\_home\_networks\_using\_openvpn\_and_openwrt/
