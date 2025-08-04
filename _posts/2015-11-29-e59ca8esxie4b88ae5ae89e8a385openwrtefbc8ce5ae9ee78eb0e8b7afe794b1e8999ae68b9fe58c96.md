---
id: 455
title: 在HP GEN8上安装openwrt，实现“万兆”虚拟路由器。。。
date: 2015-11-29 20:54:28+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
最近搞了一台HP Gen8 microserver，升级cpu，内存，Intel I350-T4口千兆网卡以后就装了个esxi，自己用ESXi-Customizer-v2.7.2把最新版的网卡驱动集成了进去，网卡驱动为igb-5.3.1-1331820-3123166，之前网友说kmod-igb支持I350，所以这次才入的I350-T4，据说转发小包性能强于I340-T4，价格还比I340便宜。。。

**目标：**

  * 通过openwrt设置vmxnet3万兆虚拟网卡通过esxi的链路聚合设置I350， 实现4Gb上行链路
**过程：** 

  * netgear GS116E V2交换机，只支持static的链路聚合lag，不支持lacp。。。双机拷贝openwrt下文件速度之和最多1900Mbps
  * 后来更新了个HP 1810-8g的设备，成功实现了distribute switch下的lacp，但是双机拷贝openwrt下文件速度之和最多仍然是1900Mbps
  * 通过监控发现，静态下和动态lacp下，走的是两个物理网口，但是速度之和为1900Mpbs（最后有截图）
  * 另外，如果I350的4个网口，直通了2个e1000，另外两个做lacp的话，当openwrt选择虚拟vmnet3时，网络是不通的，只有选择e1000才通。。。
  * 最后在I350直通了2个网口分别给2台物理机，同时拷贝openwrt速度均可以达到1000Mpbs，说明不是磁盘性能问题。
<!--more-->

  
**插曲：**

  * distribute switch在lacp模式下，虚拟机win7，使用vmxnet3网口，安装vmwaretools，双机拷贝虚拟机下文件，可以达到总共2000Mbps的速度，说明lacp配置正确。
  * 使用standard switch，交换机在static模式下，虚拟机win7，使用vmxnet3网口，安装vmwaretools，双机拷贝虚拟机下文件，可以达到总共2000Mbps的速度，说明交换机trunk配置正确。
**结论：**

  * openwrt的vmxnet3驱动后虽然暂时无法安装vmware tools但性能至少可以达到1900Mpbs
**硬件：**

  * HP Gen8 屌丝版——HP服务器做工真心好，但是主板所有接口都是反人类的非标口，主板也是非标型主板。
  * CPU升级为： E3 1230 V2
  * 内存升级为平民版：Kingston DDR3 1600 8GB ECC 惠普服务器专用内存(KTH-PL316ELV/8G) *2 共16GB
  * 电源搞了个国产的250w 小1U电源，替换了原装的150w 小1U电源，主要是它的光驱位供电居然是迷你小4pin的软驱口。。。换了电源接口多多
  * 风扇捆了2个Wind Ace D35M12 3CM 12V 0.04A ，毕竟原装散热片是35w tdp的，而1230是69w的tdp。。。
  
  <br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206114231.jpg" width="1000" height="618" alt="AltText" />
 <br>
 
  * 硬盘是之前买的西数nas红盘 放在sata1，镁光BX100 500G SSD 放在sata5，都是做成单盘raid0，否则无法从sata5启动，这样的优点是可以不用tf或者u盘引导启动，缺点是所有硬盘不可以休眠。

<br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206114902.png" width="1000" height="618" alt="AltText" />
 <br>

我用的是HP的intelligent provision，也就是ip 装的系统，这坑货不识别6.0的HP定制版的ESXi iso。。。后来才知道6.0的版本要用bundle版本才可以装，不管了，装了HP定制版VMware-ESXi-5.5.0-Update3-3116895-HP-550.9.4.26-Nov2015.iso也行，后来发现也是坑啊。

1.编译Openwrt系统img  
这个不多说了，问题在于:  
**一定要把kmod-vmxnet3，kmod-igb,kmod-e1000,kmod-e1000e编译进去，否则esxi虚拟的网卡不能用**  
**如果无需迅雷远程，可以编译x64版本的镜像，性能远超x86**  
下面有个性能对比，都是我跑出来的第一手资料，cc略强于bb，但是cc下的openvpn我编译出来运行不了，老缺个libc.so，所以最后就放弃了：

<pre class="lang:vim decode:true " >MD5 	SHA-1 	DES 	3DES 	AES-128 	RSA Sign 	RSA Verify 	DSA Sign 	DSA Verify 	OS 	SoC 	CPU 	OpenSSL Version 
422333440	157073750	52919910	19314850	66379090	61.8	2260.6	222.3	182.2	bbr46287	i3 540	x86	1.0.2d 
506805250	480641710	62921390	24199510	100739070	522	16821.8	1664.6	1364.2	ccrc3r46163	i3 540	x8664	1.0.2d
513278290	196502530	67375790	24792060	108380840	107.7	3959.3	386.6	311.7	ccr46705	vmware e3  1230v2	x86vmware	1.0.2d
512455340	193744550	66202970	24312830	105958400	105.6	3872.5	379.4	309.3	bbr46287	vmware e3  1230v2	x86vmware	1.0.2d
</pre>

我编译出来的镜像叫：openwrt-x86-generic-combined-ext4.img，是bb 14.07的版本。

2.制作vmdk 6G大镜像——也就是esxi的虚拟盘  
其实本来可以在esxi下对于现有的vmdk进行扩容，我也试过，但是每次扩容完成后，都无法启动openwrt，提示找不到盘，故采用其他方法：  
首先制作一个全0x00的二进制文件，例如6g_00.bin，然后在linux下执行：

<pre class="lang:sh decode:true " >cat openwrt-x86-generic-combined-ext4.img 6g_00.bin &gt; openwrt-x86-generic-combined-ext4-bb6g.img </pre>

这样就得到一个6G的镜像了。  
接下来就是要把img转换成vmdk，[openwrt官网有如何把img转换成vmdk的攻略](https://wiki.openwrt.org/doc/howto/vmware)，由于我用的是debian，故略有不同：

<pre class="lang:sh decode:true " >apt-get install qemu-utils
  qemu-img convert -f raw -O vmdk openwrt-x86-generic-combined-ext4-bb6g.img openwrt-x86-generic-combined-ext4-bb6g.vmdk</pre>

转换完成后的vmdk只有48MB多一些，但是加载到esxi上后就可以看到置备空间是6G多，达到了我们目的。

3.上传并安装，分区  
用vmware client把openwrt的vmdk虚拟盘上传到ssd，再把gparted-live-0.21.0-1-i586.iso上传ssd以后，就可以添加虚拟机了，首先我们要建立一个其他的虚拟机，其中光盘使用gparted-live-0.21.0-1-i586.iso引导，然后挂载openwrt的vmdk的虚拟盘进行扩展，一共分3个区，把openwrt分区拉到3G，最后一个分区也拉到3G，最后显示为类似如下图（下图是我用之前硬盘分3个区的）：  
<br>
 <img src="https://jibenfa.github.io/uploads/2015/07/IMG_20150725_202654.jpg" width="1000" height="618" alt="AltText" />
 <br>

分区完成后，关闭该虚拟机，记得移除挂载的openwrt分区。

4.创建openwrt虚拟机  
这个就很简答拉，直接添加openwrt的vmdk，然后添加2块网卡，注意都要选择vmxnet3，这样就是万兆卡了 
 
<br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151201210547.png" width="1000" height="618" alt="AltText" />
 <br>
 
 <br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151201210638.png" width="1000" height="618" alt="AltText" />
 <br>

启动openwrt，最后会看见如下图：

<pre class="lang:vim decode:true " >[    5.176918] vmxnet3 0000:03:00.0 eth0: intr type 3, mode 0, 5 vectors allocated
[    5.177585] vmxnet3 0000:03:00.0 eth0: NIC Link is Up 10000 Mbps
[    5.177744] 8021q: adding VLAN 0 to HW filter on device eth0
[    5.177824] device eth0 entered promiscuous mode
[    5.177933] br-lan: port 1(eth0) entered forwarding state
[    5.178013] br-lan: port 1(eth0) entered forwarding state
[    5.178954] vmxnet3 0000:0b:00.0 eth1: intr type 3, mode 0, 5 vectors allocated
[    5.179815] vmxnet3 0000:0b:00.0 eth1: NIC Link is Up 10000 Mbps
[    5.180439] 8021q: adding VLAN 0 to HW filter on device eth1
[    5.277329] device tap0 entered promiscuous mode</pre>

妥妥的万兆卡（实测双机拷贝最多达到总共1900Mpbs）

5.设置链路聚合  
由于openwrt不支持链路聚合，所以我用的是esxi的简单的方式实现链路聚合，基于ip哈希的策略，对于单机拷贝来说，最多1000Mbps，但是可以支持多个1000Mbps拷贝，如图：  

 <br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151201211138.jpg" width="1000" height="618" alt="AltText" />
 <br>
 
netgear上的设置也很简单，无需设置vlan，这个交换机好贵。。。

6.小插曲  
一开始搞完上述以后，我测试了一下网络，传输读写拷贝文件居然只有~100Mbps（10-15MB/s）,这不科学啊。。。于是我采用排除法，把I350网卡直通，发现还是这么慢，在乱改一同参数后，发现，不是esxi 5.5的网络慢，原来是坑爹的磁盘慢，读写只有这么点，后来查阅了大量资料，最终在[chiphell网友](http://www.chiphell.com/thread-1330699-1-1.html)和某台湾网友的帖子里面发现是板载raid卡b120i的驱动问题：Mware-ESXi-5.5.0-Update3-3116895-HP-550.9.4.26-Nov2015.iso带的scsi-hpvsa 5.5.0.100-1OEM.550.0.0.1331820 Hewlett-Packard 这个是罪魁祸首，更换为[scsi-hpvsa-5.5.0-88OEM.550.0.0.1331820.x86_64.vib](http://vibsdepot.hp.com/hpq/sep2014/esxi-550-drv-vibs/hpvsa/scsi-hpvsa-5.5.0-88OEM.550.0.0.1331820.x86_64.vib)问题解决，更换办法可以参考[chiphell网友sym的攻略](http://www.chiphell.com/thread-1330699-1-1.html),但是我最后还是使用了scsi-hpvsa-5.5.0-84OEM.550.0.0.1198611.x86_64.vib这个版本的驱动，[原因是一位台湾网友的帖子，88版本有heartbeat问题，会造成虚拟机卡顿](http://wolfriya.blogspot.jp/2015/03/hp-proliant-microserver-gen8-exsi.html)：  
先把驱动上传esxi的存储，拷贝到/var/log/vmware/,我的上传路径是vmfs/volumes/datastorage1/drviers：

<pre class="lang:sh decode:true " >cp vmfs/volumes/datastorage1/drviers/scsi-hpvsa-5.5.0-84OEM.550.0.0.1198611.x86_64.vib /var/log/vmware/</pre>

然后运行：

<pre class="lang:sh decode:true " >esxcli system maintenanceMode set --enable true</pre>

进入维护模式，然后卸载原来的驱动，大约需要几十秒：

<pre class="lang:sh decode:true " >esxcli software vib remove -n scsi-hpvsa -f</pre>

接着安装驱动：

<pre class="lang:sh decode:true " >esxcli software vib install -v file:scsi-hpvsa-5.5.0-84OEM.550.0.0.1198611.x86_64.vib --force --no-sig-check --maintenance-mode</pre>

几十秒安装完成后，重启后退出维护模式

<pre class="lang:sh decode:true " >esxcli system maintenanceMode set --enable no</pre>

然后再测试拷贝，大约就有800-900Mbps（90-100+MB/s）的速度啦。

由于gen8的板载raid卡关系，不能直通硬盘控制器，否则esxi就不能用了。。除非用pcie的raid卡，但是我的已经被网卡占了。。。。所以只能取舍了。。。

2015年12月6日更新LACP链路聚合：  
上行链路uplink配置  

<br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206095232.png" width="1000" height="618" alt="AltText" />
 <br>
 
 端口组portgroup配置 
  
<br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206095202.jpg" width="1000" height="618" alt="AltText" />
 <br>
 
 distribute switch虚拟机配置 
  
<br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206094232.png" width="1000" height="618" alt="AltText" />
 <br>
 
 HP交换机lacp配置  
 
<br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206094205.png" width="1000" height="618" alt="AltText" />
 <br>
 
 <br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206094147.png" width="1000" height="618" alt="AltText" />
 <br>
 
 <br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206094122.png" width="1000" height="618" alt="AltText" />
 <br>
 
 可以看到，6,7端口分别承担了一半的流量，在虚拟机openwrt下和在虚拟机windows下可以达到至少1900Mbps（因为只有2台机器测试）  

<br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206111438.png" width="1000" height="618" alt="AltText" />
 <br>
 
 <br>
 <img src="https://jibenfa.github.io/uploads/2015/11/QQ20151206113210.jpg" width="1000" height="618" alt="AltText" />
 <br>
 