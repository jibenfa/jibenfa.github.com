---
id: 175
title: TP-Link wr720n Openwrt 科学上网改造，使用ChinaDNS + Shadowsocks 攻略
date: 2015-03-04 21:36:09+00:00
author: coffeecat
layout: post
categories:
- openwrt
- 科学上网
tags:
- openwrt
- 科学上网
---
最近又在研究openwrt科学上网，正好手头有个TP-link wr720n v4 版本超便携路由，查阅资料以后发现，该机跟v3版本的配置一样，也就是说可以用v3版本的op的rom，由于这个路由内置存储仅有4M，完全不够用，目前有2个解决办法，1.淘宝有大神硬改，把4M flash换成了8或16M，过于彪悍了，2.软改，利用extroot让路由器从u盘启动，我是后者，使用了超mini的sandisk 16G usb3.0（向下兼容2.0）的u盘作为系统盘。一周折腾期间前前后后刷了不少大神的rom，但是都不能正常使用chinadns和shadowsocks，所有努力均以失败告终，最终使用官方rom成功。之前失败的根本原因是openwrt的kernel和软件关联性（dependence）太严格，导致就算是一个版本的kernel，编译版本不同，其很多软件都不能通用，特别是kmod开头的内核相关软件。  
如果强行安装，就会报错，一个典型的错误内容如下：

```sh
satisfy_dependencies_for: Cannot satisfy the following dependencies for kmod-usb-storage:
kernel (= 3.3.6-1-06e8dc0e21c6891eb05dce4475cadf2b) * kernel (= 3.3.6-1-06e8dc0e21c6891eb05dce4475cadf2b) * kernel (= 3.3.6-1-06e8dc0e21c6891eb05dce4475cadf2b) * kernel (= 3.3.6-1-06e8dc0e21c6891eb05dce4475cadf2b) *
```

后面那串数字，我猜就和kernel编译版本相关，就算前面大版本对了，只要小版本不对，很多软件还是装不上，必须安装同时编译好的ipk软件，由于大神们的rom总是缺一两个关键软件导致ss和chinadns无法正常工作，所以最后都得放弃。期间自己也编译过一个rom，花费了2个小时，装上以后虽然没变砖，但是使用起来效果还不好。。。

于是，只好使用官方编译好的版本的rom，怕以后对应的ipk软件找不到，我把其官网的所有3000多个ipk gz文件都下载下来了，然后自己搭了一个source。。。下面说一下流程，备忘。。

<!--more-->

# 使用的硬件包括：

a.tp link wr720n v4版本，官方rom，ip为192.168.1.253（刷了不死uboot以后变为192.168.1.1）  
b.闪迪 （SanDisk）至尊高速酷豆（CZ43) USB 3.0 U盘 16GB 读130MB/s 写20MB/s jd货  
c.牙签一根，用来捅菊花reset路由器  
d.网线一根  
e.插座一个  
f.win7 pc一台

# 使用的软件包括：

a.openwrt barrier_breaker 14.07 的wr720n v3官方rom及对应的所有packages  
b.partitionmagic 10.0绿色版  
c.EasyWebSvr-v1.9简易http服务器软件

# 软改步骤:

## 1.下载官方rom和packages

尽量不要选snapshot下的dev版本，因为不稳定，我下的是http://downloads.openwrt.org/barrier_breaker/14.07/里面的wr720n以及package下所有的ipk文件和gz文件。

## 2.搭建自己的source源，因为openwrt官网经常被抽搐，速度不敢保证，如果网络够好，这步也不用。

使用一台win pc机，设置ip为192.168.1.100，下载EasyWebSvr-v1.9.rar，解压后设置一下，把packages和包都丢到http的目录下，这样我们就有一个本地的source源了。访问http://192.168.1.100/ 看得见package目录列表就ok

## 3.刷不死uboot，如果内心够强大，这一步可以跳过。。。

可以参考http://www.right.com.cn/forum/thread-149251-1-1.html 一文中的版本刷入不死uboot，其实没必要啦。

## 4.给u盘分区

我用partitionmagic给16G的u盘分了2个区，一个是13G的ext3格式，一个是1.8G的swap格式，如果有离线下载或者samba需求的可以再分一个vfat或者ntfs分区

## 5.刷入官方rom

如果之前没刷过op，直接是从tplink的官方系统固件升级界面刷的,就使用[openwrt-ar71xx-generic-tl-wr720n-v3-squashfs-factory.bin](http://downloads.openwrt.org/barrier_breaker/14.07/ar71xx/generic/openwrt-ar71xx-generic-tl-wr720n-v3-squashfs-factory.bin)  
这个很方便，直接web界面选中该rom刷进去。。。刷的过程中不能断电，刷完以后路由器自动重启。

由于我之前刷过op，这次直接从别的op刷过来，就使用[barrier_breaker.14.07](http://downloads.openwrt.org/barrier_breaker/14.07/)下的[openwrt-ar71xx-generic-tl-wr720n-v3-squashfs-sysupgrade.bin](http://downloads.openwrt.org/barrier_breaker/14.07/ar71xx/generic/openwrt-ar71xx-generic-tl-wr720n-v3-squashfs-sysupgrade.bin)  
把bin文件放到http目录下，通过访问http://192.168.1.100/ 可以看见该rom。  
然后ssh登陆720n。执行：

```sh
cd /tmp
wget http://192.168.1.100/openwrt-ar71xx-generic-tl-wr720n-v3-squashfs-sysupgrade.bin
mtd -r write openwrt-ar71xx-generic-tl-wr720n-v3-squashfs-sysupgrade.bin firmware
```

然后开始刷入，完成后，路由器自动重启。

## 6.登陆路由器，修改密码

刷完以后，路由器默认无密码，在win7 pc上调出cmd命令行，直接执行

```sh
telnet 192.168.1.1
```

```sh
BusyBox v1.22.1 (2014-09-20 22:01:35 CEST) built-in shell (ash)
Enter 'help' for a list of built-in commands.

  _______                     ________        __
 |       |.-----.-----.-----.|  |  |  |.----.|  |_
 |   -   ||  _  |  -__|     ||  |  |  ||   _||   _|
 |_______||   __|_____|__|__||________||__|  |____|
          |__| W I R E L E S S   F R E E D O M
 -----------------------------------------------------
 BARRIER BREAKER (14.07, r42625)
 -----------------------------------------------------
  * 1/2 oz Galliano         Pour all ingredients into
  * 4 oz cold Coffee        an irish coffee mug filled
  * 1 1/2 oz Dark Rum       with crushed ice. Stir.
  * 2 tsp. Creme de Cacao
 -----------------------------------------------------
```

登陆后，修改root密码，输入

```sh
passwd root
```

输入2次密码后，密码成功修改，关闭telnet。

## 7.安装extroot挂载u盘必备软件

打开putty或者secureCRT，登陆192.168.1.1，进入shell  
首先修改opkg软件源：

```sh
vi /etc/opkg.conf
```

将src/gz开头的修改为：

```vim
src/gz barrier_breaker_base http://192.168.1.100/base
src/gz barrier_breaker_luci http://192.168.1.100/luci
src/gz barrier_breaker_packages http://192.168.1.100/packages
src/gz barrier_breaker_routing http://192.168.1.100/routing
src/gz barrier_breaker_telephony http://192.168.1.100/telephony
src/gz barrier_breaker_management http://192.168.1.100/management
src/gz barrier_breaker_oldpackages http://192.168.1.100/oldpackages
```

保存后退出。  
继续运行：

```sh
opkg update
opkg install kmod-usb-ohci kmod-usb2 kmod-fs-ext4 kmod-usb-storage block-mount 	kmod-nls-base kmod-nls-cp437 kmod-ipt-nat-extra iptables-mod-nat-extra
```

以上软件一个都不能少，特别是cp437，看起来跟挂载无关，但是没有就是不行。安装过程中会提示：  
kmod: failed to insert /lib/modules/&#8230;..  
的error不要管，回头重启了就好了。

装完上述软件后，运行：

```sh
df

```

会发现rootfs只剩下了40k，好悬啊。。。

然后关闭路由器。

## 8.挂载u盘

将格式化好的u盘插入路由器usb口，将路由器模式开关拨到3g，开启路由器。  
路由器灯不闪了，固定亮着以后，继续ssh登陆192.168.1.1  
运行

```sh
ls /dev/sda*

```

如果显示了

```sh
/dev/sda   /dev/sda1  /dev/sda2
```

说明u盘已经成功认出来了，否则拔插一下或者重新格式化。

接着运行：

```sh
block detect > /etc/config/fstab
vi /etc/config/fstab
```

修改为类似如下内容（uuid那行不要动）：

```vim
config 'global'
        option  anon_swap       '0'
        option  anon_mount      '0'
        option  auto_swap       '1'
        option  auto_mount      '1'
        option  delay_root      '5'
        option  check_fs        '0'

config 'mount'
        option  target  '/overlay'
        option  uuid    '4a639f83-8137-f649-0f2c-79d66189a4ca'
        option  fstype  ext3
        option  options rw,sync
        option  enabled '1'
        option  enabled_fsck 0

config 'swap'
        option  device  '/dev/sda2'
        option  enabled '1'
```

保存，退出。  
接着运行：

```sh
mkdir /mnt/sda1
mount /dev/sda1 /mnt/sda1
mkdir -p /tmp/cproot
mount --bind / /tmp/cproot/
tar -C /tmp/cproot/ -cvf - . | tar -C /mnt/sda1 -xf -
umount /dev/sda1
umount /tmp/cproot
echo option force_space >> /etc/opkg.conf
```

上述命令是把4M文件系统中的文件备份到u盘，这样以后就算从u盘重启失败（例如u盘被拔出），4M flash里面的东西仍然是不会被修改删除的，还是可以进入系统进行操作的。

路由器重启以后，打开chrome或者ie浏览器，输入192.168.1.1，用root进行登陆，登录后选择system->mount point，可以看见rootfs已经变为十多个G了。  
在最后的swap那边，点击‘启用’swap。  
在mount points那边找到/dev/sda1那一行，最后有个‘删除’按钮，点击删除，然后点击‘添加’：  
选择/dev/sda1 ，文件系统选择 ext3，这时候会出来一个选项，‘设置为rootfs’，选中它，再选中‘启用’，最后保存并应用。  
其实最后这2步可以不做的，但是为了好看。。。就这样吧。。。  
至此，路由器已经完成从u盘启动了，以后所有的修改，都在u盘上进行了，随便折腾，就算弄挂了，还可以拔掉u盘，从4m 内置flash启动，救回来。

## 9.安装chinadns和shadowsocks等软件。

ssh登陆路由器192.168.1.1。  
首先安装ipset:

```sh
opkg update
opkg install ipset
```

安装过程中会提示：  
kmod: failed to insert /lib/modules/&#8230;..  
的error不要管，回头重启了就好了。  
安装完成后重启路由。。。  
重启后继续ssh登陆路由器192.168.1.1。安装前置软件：

```sh
opkg update
opkg install libpolarssl
opkg install resolveip
opkg install luci-i18n-chinese
```

接着去谷歌一下如下4个软件，下载并放到http文件夹的extra目录下，并安装，注意，这几个文件都不是kernel depend的，所以可以装最新版本：

```sh
opkg install http://192.168.1.100/extra/ChinaDNS_1.3.0-1_ar71xx.ipk
opkg install http://192.168.1.100/extra/shadowsocks-libev-spec-polarssl_2.1.4-1_ar71xx.ipk
opkg install http://192.168.1.100/extra/luci-app-chinadns_1.3.1-1_all.ipk 
opkg install http://192.168.1.100/extra/luci-app-shadowsocks-spec_1.3.0-1_all.ipk
```

安装完成后在浏览器访问192.168.1.1，system->system->lanuage 选择中文。  
重启路由器。

## 10.配置shadowsocks和chinadns，增加cron计划任务

在浏览器打开192.168.1.1，发现已经是中文版了，在&#8217;服务&#8217;下也多了chinadns和shadowsocks，下面进行设置：  
服务->chinadns设置  
‘启用压缩指针’钩打上  
‘启用双向过滤’钩去掉，  
‘上游服务器’改成1.2.4.8,202.96.199.132,223.6.6.6,123.125.81.6,114.114.115.115,114.114.114.114,127.0.0.1:5151，  
‘过滤文件’修改为使用/etc/shadowsocks/ignore.list ，这跟shadowsocks使用同样的文件，这样只要维护这一个文件就行了。

服务->shadowsocks设置  
’使用配置文件’的钩去掉，直接填入远程服务器、远程端口、密码、本地端口相关的参数  
‘udp转发’选项打钩（如果服务器端shadowsocks不是最新版可能无法支持这个功能，请参考文档1中其他办法），  
‘udp本地端口’填跟chinadns中‘上游服务器’设置时候一样的，例如：5151，千万不要和chinadns本地端口的设成一样的。

网络->dhcp/dns设置  
基本设置->dns转发 里面设置为127.0.0.1#5353  
127.0.0.1#5353  
127.0.0.1#5353  
127.0.0.1#5353  
填4个是为了保证稳定性，否则经常会出现解析失败导致网页无法打开  
基本设置->host和解析文件 里面  
忽略解析文件 打钩  
忽略HOSTS文件 打钩

保存并应用。如果ss无法启动，需要如下操作：

```sh
ln -s /usr/lib/libpolarssl.so /usr/lib/libpolarssl.so.7
```

最后更新一下过滤文件，ssh登陆192.168.1.1，运行：

```sh
opkg update
opkg install libcurl curl
curl 'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest' | grep ipv4 | grep CN | awk -F\| '{ printf("%s/%d\n", $4, 32-log($5)/log(2)) }' > /etc/shadowsocks/ignore.list
```

更新完成后该文件有5000多行，至此，所有配置完成，路由器实现了动态科学上网，国内网站不用代理，国外网站使用代理，其原理我画了一张图：

[<img class="alignnone size-full wp-image-183" src="https://jibenfa.github.io/uploads/2015/03/microMsg.1425433929069.jpg" alt="microMsg.1425433929069" width="3744" height="2102" srcset="https://jibenfa.github.io/uploads/2015/03/microMsg.1425433929069.jpg 3744w, https://jibenfa.github.io/uploads/2015/03/microMsg.1425433929069-300x168.jpg 300w" sizes="(max-width: 3744px) 100vw, 3744px" />](https://jibenfa.github.io/uploads/2015/03/microMsg.1425433929069.jpg)

&nbsp;

看图就明白了。

&nbsp;

参考文档：

1.https://cokebar.info/archives/664#method1  
2.http://shadowsocks.info/shadowsocks-chinadns/  
3.openwrt官网文档