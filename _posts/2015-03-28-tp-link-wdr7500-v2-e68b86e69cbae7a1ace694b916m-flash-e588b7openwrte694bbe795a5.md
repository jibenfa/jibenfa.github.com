---
id: 269
title: TP-Link WDR7500 v2 拆机硬改16M Flash 刷openwrt攻略
date: 2015-03-28 19:21:09+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
去年入了一个TP-Link WDR7500 v2，硬件配置是目前家用顶级的，但是原厂软件就是渣，各种不稳定，后来升级到了官方固件140401测试版（2014年6月14日发布）后基本稳定，但是偶尔网络也会抽风，非常不爽，到现在还没有正式版本的固件，我也是对tplink无语了。。。  
后来到openwrt官网发现还是可以刷的（但没有了5GHz），想想为了稳定，暂时没有5GHz就算了。。  
下载了openwrt官网的固件：openwrt-ar71xx-generic-archer-c7-v1-squashfs-factory.bin ，打算开刷，发现tplink 140401固件居然封了刷机，非官方rom一律不让刷。。。降级也不行。。。我无力吐槽了。。。  
没办法，只有硬来了，国内行货版的TP-Link WDR7500 v2是外置六天线，但是flash只有8M （winbond w25Q64fv），非常不爽，也就一起搞了。

先拆掉屁股后面4个螺丝，然后用软卡撬开隐藏的塑料卡扣，左右各3个，前后各1个。  
然后就这样了（红圈的是flash，紫圈是ttl孔,焊上针脚之前是孔，图上已经是我焊好的）：  
<!--more-->
<br>
 <img src="https://jibenfa.github.io/uploads/2015/03/microMsg.1427534333592.jpg" width="1000" height="618" alt="AltText" />
 <br>
 
 <br>
 <img src="https://jibenfa.github.io/uploads/2015/03/IMG_20150328_155020_.jpg" width="1000" height="618" alt="AltText" />
 <br>
 
 <br>
 <img src="https://jibenfa.github.io/uploads/2015/03/IMG_20150328_155028_.jpg" width="1000" height="618" alt="AltText" />
 <br>
 

按照op官网说明，顺手把ttl针脚焊上去了，从左到右依次是tx,rx,gnd,vcc 3.3v：  


  <br>
 <img src="https://jibenfa.github.io/uploads/2015/03/IMG_20150328_165747_.jpg" width="1000" height="618" alt="AltText" />
 <br>
 flash在中间，周围小元件也不多，一把烙铁就拆下了，拆下后用编程器读取flash，备份官方flash 8M编程器固件：uboot，firmware和art。然后用winhex提取art.bin，到[恩山论坛](http://http://www.right.com.cn/FORUM/thread-136444-1-1.html)上下载H大大的wdr7500 uboot:u-boot-qca9558-ar8327n.bin，然后计算uboot，firmware，art的大小之和，用16M减去这个值后，得到8454144，填入我的perl脚本，生成填充文件16M_FF.bin：

```perl
#!/usr/bin/perl 
use strict;
my $i = 8454144;
open(FH,'>','16M_FF.bin');
binmode(FH);
my $xff =pack("H*","FF");
while($i>0)
{
  print FH $xff; 
  $i--; 
}

close FH;

```

最后运行：

```sh
cat u-boot-qca9558-ar8327n.bin openwrt-ar71xx-generic-archer-c7-v1-squashfs-factory.bin 16M_FF.bin art.bin > wdr7500v2fullflash16M.bin
```

然后用编程器烧录到winbond W25Q128FVSG，焊接到电路板上。 

<br>
 <img src="https://jibenfa.github.io/uploads/2015/03/IMG_20150328_165729.jpg" width="1000" height="618" alt="AltText" />
 <br>
 
 <br>
 <img src="https://jibenfa.github.io/uploads/2015/03/IMG_20150328_165734.jpg.jpg" width="1000" height="618" alt="AltText" />
 <br>
  
上电，一次成功，装完常用软件还有9M多，wifi 2.4GHz正常（不能中继），唯一缺点就是wifi 5Ghz不可用。  

<br>
 <img src="https://jibenfa.github.io/uploads/2015/03/QQ20150328193420.jpg" width="1000" height="618" alt="AltText" />
 <br>
 
 <br>
 <img src="https://jibenfa.github.io/uploads/2015/03/QQ20150328193453.png" width="1000" height="618" alt="AltText" />
 <br>
 