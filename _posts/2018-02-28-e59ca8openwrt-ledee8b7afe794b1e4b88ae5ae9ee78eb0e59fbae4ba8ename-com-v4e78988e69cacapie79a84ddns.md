---
id: 660
title: 在Openwrt/Lede路由上实现基于Name.com V4版本API的快速更新的DDNS
date: 2018-02-28 22:21:35+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
之前一直用花生壳的免费DDNS，但是最近一周不知道为啥，服务老是抽风，dns更新速度明显下降，甚至达到1-2天。于是研究了一下，发现name.com最近发布了v4版本的api，看了文档以后，果断写了个脚本，一旦ip变更，新dns可以马上更新，消耗时间无限接近0。。。于是ddns更新时间只基于计划任务的间隔时间了。。。  
使用此脚本的前提：  
1.域名必须是由name.com购买的，并且生成一个生产的Token。  
2.登陆账户必须没有开启二次验证，否则api会提示错误：Accout has Namesafe enabled. （注意这里account拼写还是错的。。已发ticket给name.com）。  
3.路由上需要安装curl和ca-certificates和ca-bundle,以便解析https。  
4.首次需要手动添加一次域名，以便获取ID号码，例如为www.examle.com添加第一个dns记录：  
<!--more-->

```sh
curl -u 'YOUR_USER_NAME:YOUR_API_TOKEN' 'https://api.name.com/v4/domains/example.com/records' -X POST --data '{"host":"www","type":"A","answer":"YOUR_IP","ttl":300}'
```

从返回的json里面记录下id，json格式为：

```sh
{
    "id": 12345,
    "domainName": "example.org",
    "host": "www",
    "fqdn": "www.example.org",
    "type": "A",
    "answer": "10.0.0.1",
    "ttl": 300
}
```

此id要写入脚本。

后续就可以通过如下脚本更新dns了。  
脚本如下：

```vim
#!/bin/sh

USER="YOUR_USER_NAME"
TOKEN="YOUR_API_TOKEN"
ID="YOUR_URL_ID"
HOST="www"
DOMAIN="example.com"
URL=${HOST}.${DOMAIN}
IP=`ping ${URL} -c 1 |awk 'NR==2 {print $4}' |awk -F ':' '{print $1}'`
#如果安装了dig也可以这样
#IP=`dig ${DOMAIN} @114.114.114.114 | awk -F "[ ]+" '/IN/{print $1}' | awk 'NR==2 {print $5}'`
echo "Ip of ${URL} is ${IP}"
LIP=`ifconfig pppoe-wan|awk -F "[: ]+" '/inet addr/{print $4}'`
echo "Local Ip is ---${LIP}---"

if [ "${LIP}" = "${IP}" ]; then
   exit
fi

echo "start ddns refresh"
if [ x"${LIP}" != x ]; then
   curl -u ''""${USER}""':'""${TOKEN}""'' 'https://api.name.com/v4/domains/'""${DOMAIN}""'/records/'""${ID}""'' -X PUT --data '{"host":"'""${HOST}""'","type":"A","answer":"'""${LIP}""'","ttl":300}'
   echo ${LIP} > /tmp/ddnsResult
fi
```

参考资料：  
1.https://www.name.com/api-docs/