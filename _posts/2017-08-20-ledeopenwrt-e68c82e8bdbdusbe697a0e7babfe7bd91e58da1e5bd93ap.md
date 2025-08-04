---
id: 644
title: LEDE/Openwrt 挂载USB无线网卡当AP
date: 2017-08-20 12:42:57+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
由于mt7621方案中mt7603e的2.4G lede驱动非常不稳定，导致我买的newifi d1、zbt wg3526、极路由4（HC5962）刷机后的2.4G基本都成了摆设。没办法只能通过挂载USB无线网卡当AP。  
测试的USB网卡有：  
X东购买tplink tl-wn725n v2.0 rtl8188eu （0x0bda:0x8179）安装驱动后直接无法启动路由器。。。跟作者发了邮件，回复说不支持。  
X宝购买RT3070 杂牌网卡，安装驱动后直接无法开启ap模式，只能使用client模式。。。网上查询据说是最新的几版的驱动有问题，op老版本据说没问题，未测试。  
X东购买磊科（netcore）NW362，rtl8192cu，安装驱动后完美ap模式。  
以前买的tplink tl-wn821n v2.0，ar9170，安装kmod-carl9170驱动后，完美ap模式。