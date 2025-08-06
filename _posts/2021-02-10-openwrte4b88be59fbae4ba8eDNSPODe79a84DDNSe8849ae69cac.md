---
id: 779
title: openwrt下基于DNSPOD的DDNS脚本
date: 2021-02-10 07:25:57+00:00
author: coffeecat
layout: post
categories:
- openwrt
- 编程
tags:
- openwrt
- 编程
---

换dns供应商了，撸了一个openwrt下基于dnspod api的ddns脚本：

<pre><code class="language-bash">
#!/bin/sh

TOKEN="xxx,xxxxxxxxxxxxxxx"
DOMAIN_ID="xxxxxxxxx"
SUB_DOMAIN="xxxx"
MAIN_DOMAIN="xxxx"
DOMAIN=${SUB_DOMAIN}.${MAIN_DOMAIN}
RECORD_ID="xxxxxx"
#record_id is binding with sub_domain and main_domain, using following command to get record_id
#curl -X POST https://dnsapi.cn/Record.List -d 'login_token=${TOKEN}&format=json&domain_id=${DOMAIN_ID}&offset=0&length=3'

#get domain ip from common dns
IP=`dig ${DOMAIN} @114.114.114.114 | awk -F "[ ]+" '/IN/{print $1}' | awk 'NR==2 {print $5}'`
echo "Ip of ${DOMAIN} is ---${IP}---"

#get local ip from wan port
LIP=`ifconfig pppoe-wan|awk -F "[: ]+" '/inet addr/{print $4}'`
echo "Local Ip is ---${LIP}---"

#if domain ip and local ip are identical, dns is ok
if [ "${LIP}" == "${IP}" ]; then
   echo "Doman IP not changed."
   exit
fi

#if not identical, check dns record from ddns service provider
echo "check dnspod dns record of ${DOMAIN}"
query_cmd="curl -X POST https://dnsapi.cn/Record.Info -d 'login_token=${TOKEN}&format=json&domain_id=${DOMAIN_ID}&record_id=${RECORD_ID}'"
query_result=`eval ${query_cmd}`
query_result_sub_str=`echo "${query_result}" | grep ${LIP}`

#if dns record is ok, there is no need to update
if [ ${#query_result_sub_str} -gt 6 ]; then
   echo "IP record is OK, waiting for dns spread"
   exit
fi

#if dns record is not ok, start ddns refresh
echo "start ddns refresh"
refresh_cmd="curl -X POST https://dnsapi.cn/Record.Ddns -d 'login_token=${TOKEN}&format=json&domain_id=${DOMAIN_ID}&record_id=${RECORD_ID}&record_line_id=0&value=${LIP}&sub_domain=${SUB_DOMAIN}'"
refreah_result=`eval ${refresh_cmd}`
echo "${refreah_result}"
</code></pre>