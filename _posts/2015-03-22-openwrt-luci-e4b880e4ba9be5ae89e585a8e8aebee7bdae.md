---
id: 254
title: Openwrt 路由器管理界面登陆的一些安全设置
date: 2015-03-22 00:02:44+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
1.关闭wan远程的http(s)登陆uhttpd的Luci的web管理界面

```sh
vi /etc/config/uhttpd
```

修改为：

```vim
config uhttpd 'main'
        list listen_http '192.168.1.1:80'
        #list listen_http '[::]:80'
        list listen_https '192.168.1.1:443'
        #list listen_https '[::]:443'
```

2.启用lan本地的https登陆uhttpd的Luci的web管理界面

```sh
opkg install openssl-util luci-ssl

vi /etc/config/uhttpd
```

默认应该是：

```vim
…
option cert '/etc/uhttpd.crt'
option key '/etc/uhttpd.key'
…
```

生成对应的key和证书文件，其中第二步随便填。。。10年证书。

```sh
cd /etc
openssl genrsa 1024 > uhttpd.key
openssl req -new -key uhttpd.key > uhttpd.csr
openssl req -x509 -days 3650 -key uhttpd.key -in uhttpd.csr > uhttpd.crt
```

最后重启服务：  
/etc/init.d/uhttpd restart  
就可以访问https://192.168.1.1了，虽然会有warning，但是还是安全很多。