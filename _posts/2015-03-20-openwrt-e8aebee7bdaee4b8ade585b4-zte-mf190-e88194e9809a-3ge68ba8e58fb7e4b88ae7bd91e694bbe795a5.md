---
id: 236
title: Openwrt 设置中兴 ZTE MF190 联通 3G拨号上网攻略
date: 2015-03-20T15:27:52+00:00
author: coffeecat
layout: post


categories:


---
首先沉痛哀悼我的tplink wr720n，因为我换ram的时候，弄断了3根电路板上的焊盘引脚，导致挂了。。。  
后来买了gl-inet 16M版本的小路由，直接ssh登陆mtd -r write刷了720n的op，完全好用。折腾成功在其上的3G上网，记录一下：

1.安装必要的软件：

<pre class="lang:sh decode:true " >opkg update
opkg install ppp chat comgt luci-proto-3g kmod-usb-serial kmod-usb-serial-option kmod-usb-serial-wwan usb-modeswitch kmod-usb-serial-wwan kmod-usb-acm kmod-usb2 kmod-usb-ohci kmod-usb-uhci sdparm</pre>

注：usb-modeswitch-data 已经在14.07版本中与usb-modeswitch合并了，所以不需要了，后面设置也与前几个版本不太相同。  
<!--more-->

2.查看中兴 ZTE MF190 上网卡的vid和pid  
就算都是叫MF190，其pid也有可能不同，如何查看呢，其实很简单，把它插到windows电脑的usb口，安装完驱动以后，在‘控制面板’-‘设备管理器’里面找到该设备，‘属性’-‘硬件ID’里面就有，记录下来，我的vendor=0x19d2 product=0x0117。

3.将上网卡插到路由器usb口，并重启路由器，重启完成后，进行如下操作：

<pre class="lang:sh decode:true " >cd /dev
ls</pre>

如果有ttlUSB0，ttlUSB1，ttlUSB2设备说明识别了，否则说明上网卡有问题。

但是光识别没用，因为：

<pre class="lang:sh decode:true " >vi /etc/usb-mode.json</pre>

发现压根木有‘19d2:0117’这个硬件，这也是为啥我之前拨号都失败的原因，解决办法为：  
由于看到别的网友的mf190是1224的，所以我就复制：

<pre class="lang:vim decode:true " >"19d2:1224": {
			"*": {
				"t_vendor": 6610,
				"t_product": [ 130 ],
				"mode": "StandardEject",
				"msg": [  ]
			}
		},</pre>

修改为：

<pre class="lang:vim decode:true " >"19d2:0117": {
			"*": {
				"t_vendor": 6610,
				"t_product": [ 130 ],
				"mode": "StandardEject",
				"msg": [  ]
			}
		},</pre>

贴入/etc/usb-mode.json，保存退出。

3.按照[**官网攻略**](http://wiki.openwrt.org/doc/recipes/3gdongle)将vid和pid写入new_id并自启动写入：

<pre class="lang:sh decode:true " >vi /etc/rc.local</pre>

在exit 0前加入

<pre class="lang:vim decode:true " >echo '19d2 0117 ff' &gt; /sys/bus/usb-serial/drivers/option1/new_id</pre>

保存退出，重启路由。

4.打开192.168.1.1，找到接口，添加一个接口叫‘3g’，内容为：

[<img src="https://jibenfa.github.io/uploads/2015/03/QQ20150320151246.png" alt="QQ图片20150320151246" width="464" height="571" class="alignnone size-full wp-image-238" srcset="https://jibenfa.github.io/uploads/2015/03/QQ图片20150320151246.png 464w, https://jibenfa.github.io/uploads/2015/03/QQ20150320151246-244x300.png 244w" sizes="(max-width: 464px) 100vw, 464px" />](https://jibenfa.github.io/uploads/2015/03/QQ20150320151246.png)

保存并应用后查看系统日志。

<pre class="lang:vim decode:true " >Fri Mar 20 12:45:06 2015 daemon.notice pppd[7400]: pppd 2.4.7 started by root, uid 0
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: abort on (BUSY)
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: abort on (NO CARRIER)
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: abort on (ERROR)
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: report (CONNECT)
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: timeout set to 30 seconds
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: send (AT&F^M)
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: expect (OK)
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: AT&F^M^M
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: OK
Fri Mar 20 12:45:07 2015 local2.info chat[7402]:  -- got it
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: send (ATE1^M)
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: expect (OK)
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: ^M
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: ATE1^M^M
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: OK
Fri Mar 20 12:45:07 2015 local2.info chat[7402]:  -- got it
Fri Mar 20 12:45:07 2015 local2.info chat[7402]: send (AT+CGDCONT=1,"IP","3gnet"^M)
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: timeout set to 30 seconds
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: expect (OK)
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: ^M
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: AT+CGDCONT=1,"IP","3gnet"^M^M
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: OK
Fri Mar 20 12:45:08 2015 local2.info chat[7402]:  -- got it
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: send (ATD*99#^M)
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: expect (CONNECT)
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: ^M
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: ATD*99#^M^M
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: CONNECT
Fri Mar 20 12:45:08 2015 local2.info chat[7402]:  -- got it
Fri Mar 20 12:45:08 2015 local2.info chat[7402]: send (^M)
Fri Mar 20 12:45:08 2015 daemon.info pppd[7400]: Serial connection established.
Fri Mar 20 12:45:08 2015 daemon.info pppd[7400]: Using interface 3g-3g
Fri Mar 20 12:45:08 2015 daemon.notice pppd[7400]: Connect: 3g-3g &lt;--&gt; /dev/ttyUSB2</pre>

注意，这里的拨号脚本为/etc/chatscripts/3g.chat，因为我是联通，所以拨号脚本如下：

<pre class="lang:vim decode:true " >ABORT   BUSY
ABORT   'NO CARRIER'
ABORT   ERROR
REPORT  CONNECT
TIMEOUT 30
""      "AT&F"
OK      "ATE1"
OK      'AT+CGDCONT=1,"IP","$USE_APN"'
SAY     "Calling UMTS/GPRS"
TIMEOUT 30
OK      "ATD*99#"
CONNECT ''</pre>

<br>
<img src="https://jibenfa.github.io/uploads/2015/03/IMG_20150320_153346.jpg" width="1000" height="618" alt="AltText" />
<br>