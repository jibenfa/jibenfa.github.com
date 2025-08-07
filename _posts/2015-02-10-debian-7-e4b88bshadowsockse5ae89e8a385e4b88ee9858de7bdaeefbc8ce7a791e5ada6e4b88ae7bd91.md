---
id: 58
title: Debian 7 下Shadowsocks安装与配置，科学上网
date: 2015-02-10 12:24:11+00:00
author: coffeecat
layout: post
categories:
- linux
- 科学上网
tags:
- linux
- 科学上网
---
大部分参考 http://www.cnblogs.com/hongchenok/p/3790370.html 攻略，增加了多用户实现

比起L2TP和IPSEC是二三层的VPN，ShadowSocks则是SOCKS5——会话层的VPN，是轻量级的隧道，由于其客户端自带动态路由选择，且在不稳定网络下表现良好，特别适合移动设备例如安卓、IOS使用。下面就是安装攻略：  
在Debian 7 下，首先安装libssl

1.下载 http://ftp.br.debian.org/debian-security/pool/updates/main/o/openssl/libssl0.9.8\_0.9.8o-4squeeze14\_amd64.deb

2.安装deb包

```perl
dpkg -i libssl0.9.8_0.9.8o-4squeeze14_amd64.deb
```

3.追加软件源  
<!--more-->

```perl
vi /etc/apt/sources.list
```

在后面添加如下源

```sh
deb http://shadowsocks.org/debian squeeze main
```

然后更新源并安装

```sh
apt-get update
apt-get install shadowsocks


```

4.配置shadowsocks

```sh
vi /etc/shadowsocks/config.json
{
          "server":"vps的ip",
          "server_port":8388,
          "local_port":1080,
          "password":"ccc", 
          "timeout":60,
          "method":"aes-256-cfb" #加密方式，默认table，推荐aes-256-cfb
}
```

如果想用除table以外的加密方式，需要额外安装M2Crypto

```sh
apt-get install python-m2crypto
```

5、重启shadowsocks服务。

```sh
/etc/init.d/shadowsocks stop
/etc/init.d/shadowsocks start

update-rc.d shadowsocks defaults
```

使用shadowsocks  
windows环境下需要下载客户端：http://sourceforge.net/projects/shadowsocksgui/files/dist/ 填入之前配置的参数，保存运行即可。 新建浏览器代理为如下：

协议： socks5  
地址： 127.0.0.1  
端口： 刚才填的 local_port  
推荐配合 AutoProxy 或者 Proxy SwitchySharp 一起使用。

6. 安全设置  
新建一个低权限用户shadowsocksuser，（无密码，无法登陆，无home dir）

```sh
adduser --system --disabled-password --disabled-login --no-create-home shadowsocksuser
```

修改 /etc/default/shadowsocks

```vim
USER=shadowsocksuser
GROUP=nogroup
```

让非root用户的shadowsocks运行在1024以下端口，适用于debian 7

```sh
apt-get install libcap2-bin
setcap 'cap_net_bind_service=+ep' /usr/bin/ss-server

```

修改 /etc/init.d/shadowsocks

```sh
vi /etc/init.d/shadowsocks
```

在 ulimit -n ${MAXFD} 下直接加入

```vim
ulimit -n 51200

```

把 -c &#8220;$CONFFILE&#8221; -a &#8220;$USER&#8221; -u -f $PIDFILE $DAEMON_ARGS \ 修改为 

```vim
-c "$CONFFILE" -a "$USER" -u -f $PIDFILE $DAEMON_ARGS --forbidden-ip 127.0.0.1,::1 \
```

7.多用户支持，拷贝多份/etc/shadowsocks/config.json就是多个

```bash
multiuserSS_sh="/etc/init.d/multiuserShadowssocks.sh"
if [ -f $multiuserSS_sh ]; then
cp $multiuserSS_sh $multiuserSS_sh.bak
fi
touch $multiuserSS_sh
chmod +x $multiuserSS_sh
echo "
#!/bin/sh
### BEGIN INIT INFO
# Provides:          multiuserShadowsocks.sh
# Required-Start:    $local_fs $remote_fs $network $syslog
# Required-Stop:     $local_fs $remote_fs $network $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: multiuserSS
# Description:       shadowsocks support multiuser
### END INIT INFO
/usr/bin/ss-server -c /etc/shadowsocks/config1.json -a shadowsocksuser -u -f /var/run/shadowsocks/shadowsocks1.pid --forbidden-ip 127.0.0.1,::1

/usr/bin/ss-server -c /etc/shadowsocks/config2.json -a shadowsocksuser -u -f /var/run/shadowsocks/shadowsocks2.pid --forbidden-ip 127.0.0.1,::1
" > $multiuserSS_sh
```

7.最后

```sh
update-rc.d multiuserShadowssocks.sh defaults
```

8.补充python版的shadowsock安装：  
查看版本：

```sh
python --version
```

官网说2.6或2.7

安装：

```sh
pip install shadowsocks
```

编辑：

```bash
multiuserSS_sh="/etc/init.d/multiuserShadowssocks.sh"
if [ -f $multiuserSS_sh ]; then
cp $multiuserSS_sh $multiuserSS_sh.bak
fi
touch $multiuserSS_sh
chmod +x $multiuserSS_sh
echo "
#!/bin/sh
### BEGIN INIT INFO
# Provides:          multiuserShadowsocks.sh
# Required-Start:    $local_fs $remote_fs $network $syslog
# Required-Stop:     $local_fs $remote_fs $network $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: multiuserSS
# Description:       shadowsocks support multiuser
### END INIT INFO
/usr/local/bin/ssserver --user shadowsocksuser -c /etc/shadowsocks/config1.json --forbidden-ip 127.0.0.1,::1 -d start

/usr/local/bin/ssserver --user shadowsocksuser -c /etc/shadowsocks/config2.json --forbidden-ip 127.0.0.1,::1 -d start
" > $multiuserSS_sh
```