---
id: 608
title: 使用uClibc Toolchain编译LEDE系统，适配迅雷xware远程下载
date: 2017-02-18 21:44:38+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
最近买了MT7621路由，还带sata口，就想适配一个系统，由于：  
1.Openwrt官方trunk里面kmod-mt76驱动居然还停留在2016年6月，实测2.4G比较弱，所以不予考虑了，再看LEDE的snapshot，更新到2017年2月了，当然要选择LEDE了。  
2.LEDE目前全面切换到了MUSL库，导致迅雷xware mipsel的32位uclibc版本直接不能用了，为了适配，所以必须编译一个基于uClibc库的系统，但是LEDE/OPENWRT的toolchain默认菜单里面都只有musl和glibc了，uclibc被标记为了broken。。。。所以必须自行研究。

折腾了大约1周，终于搞定了，步骤如下：  
**1.下载LEDE源码，这个很简单：**  
<!--more-->

<pre class="lang:sh decode:true " >git clone https://git.lede-project.org/source.git
cd source
./scripts/feeds update -a
./scripts/feeds install -a</pre>

**2.修改Toolchain，以便使用uClibc：**  
(1).修改/toolchain/Config.in

<pre class="lang:vim decode:true " >--- a/toolchain/Config.in
+++ b/toolchain/Config.in
 
 	config LIBC_USE_UCLIBC
 		select USE_UCLIBC
-		bool "Use uClibc"
+		bool "Use uClibc-ng"
 		depends on !(aarch64 || aarch64_be)
-		depends on BROKEN || !(arm || armeb || i386 || x86_64 || mips || mipsel || mips64 || mips64el || powerpc)</pre>

(2).修改/toolchain/uClibc/Makefile 

<pre class="lang:vim decode:true " >--- a/toolchain/uClibc/Makefile
+++ b/toolchain/uClibc/Makefile

 define Host/SetToolchainInfo
 	$(SED) 's,^\(LIBC_TYPE\)=.*,\1=$(PKG_NAME),' $(TOOLCHAIN_DIR)/info.mk
-	$(SED) 's,^\(LIBC_URL\)=.*,\1=http://www.uclibc.org/,' $(TOOLCHAIN_DIR)/info.mk
+	$(SED) 's,^\(LIBC_URL\)=.*,\1=http://www.uclibc-ng.org/,' $(TOOLCHAIN_DIR)/info.mk
 	$(SED) 's,^\(LIBC_VERSION\)=.*,\1=$(PKG_VERSION),' $(TOOLCHAIN_DIR)/info.mk
 	$(SED) 's,^\(LIBC_SO_VERSION\)=.*,\1=$(LIBC_SO_VERSION),' $(TOOLCHAIN_DIR)/info.mk
 endef</pre>

(3).修改toolchain/uClibc/headers/Makefile

<pre class="lang:vim decode:true " >--- a/toolchain/uClibc/headers/Makefile
+++ b/toolchain/uClibc/headers/Makefile
 
 		CC="$(TARGET_CC)" \
 		CPU_CFLAGS="$(TARGET_CFLAGS)" \
 		ARCH="$(CONFIG_ARCH)" \
-		pregen \
 		install_headers
 endef</pre>

(4).如果要修改使用的uclibc-ng版本，需要修改toolchain/uClibc/common.mk里面的版本号和对应sha值，默认1.0.22不用修改了。

上述修改完成后，后续make menuconfig里面就可以选择到uclibc-ng了。

**3.编译系统**

<pre class="lang:sh decode:true " >make menuconfig</pre>

通过advanced configuration options (for developers) > Toolchain Options > c library > uclibc-ng  
其他自己选择。保存.config后，输入：

<pre class="lang:sh decode:true " >nohup ./autocompile.sh &</pre>

自动编译脚本autocompile.sh 内容为：

<pre class="lang:vim decode:true " >if [ "$1" != "-f" ] ; then
        IGNORE_ERRORS=1 make 2&gt;&1| tee errors.txt

        rm build_*.txt
fi

for i in $(grep "failed to build" errors.txt | sed 's/^.*ERROR:[[:space:]]*\([^[:space:]].*\) failed to build.*$/\1/' ) ; do
        if [ "$i" != "" ] ; then
                echo Compiling: ${i}
                make ${i}-compile V=99 &gt; build_${i##*/}.txt 2&gt;&1 || echo ${i} : Build failed, see build_${i##*/}.txt
        fi
done
</pre>

等几个小时以后就可以在source/bin目录下找到编译完成的系统了，编译过程中另外一个ssh登录，通过errors.txt和nohup.out查看编译进度，原ssh窗口可以关闭。

**4.安装系统，配置调试迅雷**  
可以通过命令行sysupgrade -v xxxx.bin或者通过luci网页升级系统。  
升级完成后，由于uclibc-ng 1.0.18及之后版本将libpthread, libcrypt, libdl, libm, libutil等库合并到了libuClibc中，需要link一些libuClibc，以便迅雷xware可以使用：

<pre class="lang:sh decode:true " >cd /lib
ln -s libuClibc-1.0.22.so libdl.so.0
ln -s libuClibc-1.0.22.so  libpthread.so.0 </pre>

然后将Xware1.0.31\_mipsel\_32_uclibc上传路由，运行:

<pre class="lang:sh decode:true " >root@LEDE:~/xunlei# ./portal
initing...
try stopping xunlei service first...
killall: ETMDaemon: no process killed
killall: EmbedThunderManager: no process killed
killall: vod_httpserver: no process killed
setting xunlei runtime env...
port: 9000 is usable.

YOUR CONTROL PORT IS: 9000

starting xunlei service...
etm path: /root/xunlei
execv: /root/xunlei/lib/ETMDaemon.

getting xunlei service info...
Connecting to 127.0.0.1:9000 (127.0.0.1:9000)

THE ACTIVE CODE IS: </pre>

常用软件例如chinadns可使用imagebuilder编译。  
**</p> 

参考文档：  
1.http://lists.infradead.org/pipermail/lede-dev/2016-June/001145.html  
2.https://lists.openwrt.org/pipermail/openwrt-devel/2009-June/004411.html  
3.https://www.mail-archive.com/lede-dev@lists.infradead.org/msg05838.html