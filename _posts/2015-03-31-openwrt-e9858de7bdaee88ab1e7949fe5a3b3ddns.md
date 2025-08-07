---
id: 291
title: Openwrt 配置花生壳DDNS
date: 2015-03-31 22:29:13+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
两种办法：  
1.通过luci配置

```sh
opkg update
opkg install luci-app-ddns ddns-scripts
```

然后在luci界面中‘更新的url’填入：

```vim
http://[username]:[password]@ddns.oray.com:80/ph/update?hostname=[domain]&myip=[ip]
```

其他按照要求填写，注意：‘ip地址来源’选‘接口’，‘接口’ 选‘pppoe-wan’

但是上述方法很不稳定。。。。有时ok有时不行。。

2.脚本办法  
转载自 http://iloss.me/post/fen-xiang/2014-01-10-openwrt-ddns 有修改

先写一个sh脚本：(路径)

```sh
vi /etc/hotplug.d/iface/25-Oray
```

内容如下：

```vim
#!/bin/sh

USER="***********"
PASS="******"
DOMAIN="*******.net"
IP=`ping ${DOMAIN} -c 1 |awk 'NR==2 {print $4}' |awk -F ':' '{print $1}'`
#如果安装了dig也可以这样
#IP=`dig ${DOMAIN} @114.114.114.114 | awk -F "[ ]+" '/IN/{print $1}' | awk 'NR==2 {print $5}'`
echo "Ip of ${DOMAIN} is ${IP}"
LIP=`ifconfig pppoe-wan|awk -F "[: ]+" '/inet addr/{print $4}'`
echo "Local Ip is ---${LIP}---"

if [ "${LIP}" = "${IP}" ]; then
   exit
fi

echo "start ddns refresh"
URL="http://${USER}:${PASS}@ddns.oray.com:80/ph/update?hostname=${DOMAIN}&myip=${LIP}"
wget -q -O /tmp/orayddnsResult -q ${URL}

```

<del datetime="2017-07-28T14:47:43+00:00">大概意思就是当路由器的ip和上一次保存在临时文件里的ip不一样的时候就访问花生壳网站更新ip</del>  
2017-07-28更新了代码，采用ping的方式，如果返回的ip与get发送的ip不一致时，重新发送。

给文件增加执行权限

```sh
chmod a+x /etc/hotplug.d/iface/25-Oray
```

给路由增加一个定时任务，每隔一分钟执行一次上面的脚本

```sh
echo */1 * * * * /etc/hotplug.d/iface/25-Oray start>> /etc/crontabs/root
```