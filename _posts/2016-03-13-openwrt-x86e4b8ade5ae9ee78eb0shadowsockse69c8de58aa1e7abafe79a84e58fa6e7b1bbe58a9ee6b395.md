---
id: 512
title: Openwrt X86中安装Shadowsocks服务端的另类办法
date: 2016-03-13 23:03:30+00:00
author: coffeecat
layout: post
categories:
- openwrt
- 科学上网
tags:
- openwrt
- 科学上网
---
之前在Openwrt x86中安装了Shadowsocks客户端（废话么），并通过openwrt下的debootstap+debian虚拟机安装了adbyby广告过滤。  
虽然在openwrt x86下原生有ss服务器端（编译时需修改makefile参数），但是据说由于架构原因，性能不行，速度最多几百K,所以同样考虑在openwrt下的debootstap+debian虚拟机实现SS服务端功能，并且与openwrt x86原生的ss客户端不冲突。。。  
该功能的主要需求是：从任何地点，通过网络，利用ios(需root)或安卓（需root）或者pc设备访问家中局域网。。。之前pc端可以通过openvpn连回家，但是安卓设备上不支持tap模式，故还需要一个轻量级的办法。。。

首先ssh登陆openwrt x86，然后：

```sh
chroot /mnt/sda3 /bin/bash
```

这样便进入了debian虚拟机shell，然后运行：

```sh
apt-get update
apt-get install python-pip
pip install shadowsocks
adduser --system --disabled-password --disabled-login --no-create-home shadowsocksuser
cd /root
vi ss.sh
```

ss.sh内容为：

```vim
#!/bin/sh

/usr/local/bin/ssserver --user shadowsocksuser -c /etc/shadowsocks.json --forbidden-ip 127.0.0.1,::1 -d start
```

```sh
chmod +x ss.sh

vi /etc/shadowsocks.json
```

内容为：

```vim
{
          "server":"0.0.0.0",
          "server_port":8388,
          "local_port":1080,
          "password":"ccc", 
          "timeout":60,
          "method":"aes-256-cfb"  
}

```

退出虚拟机，返回原生的openwrt x86 shell下

```sh
exit
```

```sh
vi /root/startss.sh
```

```vim
#!/bin/sh
chroot /mnt/sda3 /bin/bash -c "/root/ss.sh"
```

```sh
chmod +x /root/startss.sh
```

最后注意在防火墙打开端口，以下语句可以写入防火墙启动项：

```vim
iptables -I INPUT 1 -p tcp --dport 8388 -j ACCEPT
iptables -I INPUT 1 -p udp --dport 8388 -j ACCEPT

```

然后在/etc/rc.local中加入：

```sh
/root/startss.sh
```

重启路由，正常情况下就可以看到ssserver进程了。。