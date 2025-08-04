---
id: 628
title: 直插SIM卡全网五模便携LEDE路由（5200mAh）
date: 2017-03-19 11:42:02+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
之前买了个ZTE Q7便携路由，也可以刷op，但是不能直接插sim卡，携带不是很方便，最近在网上逛了逛，发现了一个神器，配置为 mt7620a ROM 16M/RAM 128M 5200mAh，花了一周时间，适配了LEDE 17.07.0 正式版本系统，目前实现了几个功能：  
1.直插sim卡上网，目前测试了移动3g和联通3g，使用的是上海移远EC20-C 4g mini pcie模块（注意经研究该模块有很多个批次，需要芯片为高通MDM9215才行，pid 05c6 vid 9215），参数为：  
EC20-C

<pre class="lang:vim decode:true " >FDD LTE: B1/B3/B8
TDD LTE: B38/B39/B40/B41
TDSCDMA: B34/B39
UMTS: B1/B8
GSM: 900/1800MHz</pre>

<!--more-->

<br>
 <img src="https://jibenfa.github.io/uploads/2017/03/IMG_20170319_104102.jpg" width="1000" height="618" alt="AltText" />
 <br>
  
参数是支持（移动4g 3g 2g，联通4g 3g 2g，电信4g）  
原厂OP可以支持EC20-CE（高通MDM9215，pid 05c6 vid 9215，注意此CE支持电信3g）但不支持EC20-CE（高通MDM9x07，pid 2c7c vid 0125）  
EC20-CE

<pre class="lang:vim decode:true " >FDD LTE: B1/B3 
TDD LTE: B38/B39/B40/B41 
TDSCDMA: B34/B39 
WCDMA: B1 
CDMA2000 1x/EVDO: BC0 
GSM: 900/1800MHz </pre>

目前LEDE 17.07是4.4的kernel，开源驱动仅支持EC20-C 4g模块（芯片为高通MDM9215，pid 05c6 vid 9215），查阅linux kernel qmi_wwan.c源代码，4.10可以支持EC20-CE（高通MDM9x07，pid 2c7c vid 0125），但目前LEDE还不行。  
2.直插SD卡，但是根据原厂说明，usb仅限对外充电，不支持外挂U盘  
3.LEDE/OPENWRT的其他功能，例如ss等

适配采用修改ZTE-Q7代码来实现（led在系统启动的时候是不亮的，启动成功后显示蓝色，囧）：  
1.修改target/linux/ramips/base-files/etc/board.d/01_leds

<pre class="lang:vim decode:true " >zte-q7)
	ucidef_set_led_default "power" "power" "$board:green:sys" "0"
	;;</pre>

2.修改target/linux/ramips/base-files/etc/diag.sh

<pre class="lang:vim decode:true " >zte-q7)
		status_led="$board:green:wifi"
		;;</pre>

3.修改target/linux/ramips/dts/ZTE-Q7.dts

<pre class="lang:vim decode:true " >/dts-v1/;

#include "mt7620a.dtsi"

#include &lt;dt-bindings/input/input.h&gt;

/ {
	compatible = "ZTE-Q7", "ralink,mt7620a-soc";
	model = "ZTE Q7";

	gpio-leds {
		compatible = "gpio-leds";

		usb {
			label = "zte-q7:usb";
			gpios = &lt;&gpio0 11 1&gt;;
		};
		sys {
			label = "zte-q7:sys";
			gpios = &lt;&gpio1 14 1&gt;;
		};
		wlan {
			label = "zte-q7:wlan";
			gpios = &lt;&gpio3 0 1&gt;;
		};
		wps {
			label = "zte-q7:wps";
			gpios = &lt;&gpio1 15 0&gt;;
		};
	};

	gpio-keys-polled {
		compatible = "gpio-keys-polled";
		#address-cells = &lt;1&gt;;
		#size-cells = &lt;0&gt;;
		poll-interval = &lt;20&gt;;

		reset {
			label = "reset";
			gpios = &lt;&gpio0 1 0&gt;;
			linux,code = &lt;0x198&gt;;
		};
	};
};

&gpio0 {
	status = "okay";
};

&gpio1 {
	status = "okay";
};

&gpio3 {
	status = "okay";
};

&spi0 {
	status = "okay";

	en25q128@0 {
		#address-cells = &lt;1&gt;;
		#size-cells = &lt;1&gt;;
		compatible = "w25q128";
		reg = &lt;0&gt;;
		linux,modalias = "m25p80";
		spi-max-frequency = &lt;10000000&gt;;

		partition@0 {
			label = "u-boot";
			reg = &lt;0x0 0x30000&gt;;
			read-only;
		};

		partition@30000 {
			label = "u-boot-env";
			reg = &lt;0x30000 0x10000&gt;;
			read-only;
		};

		factory: partition@40000 {
			label = "factory";
			reg = &lt;0x40000 0x10000&gt;;
			read-only;
		};

		partition@50000 {
			label = "firmware";
			reg = &lt;0x50000 0xfb0000&gt;;
		};
	};
};

&pinctrl {
	state_default: pinctrl0 {
		gpio {
				ralink,group ="i2c", "uartf", "wled", "spi refclk";
				ralink,function = "gpio";
			};
                        pa {
                                ralink,group = "pa";
                                ralink,function = "pa";
                        };
	};
};

&ethernet {
	pinctrl-names = "default";
	pinctrl-0 = &lt;&ephy_pins&gt;;
	mtd-mac-address = &lt;&factory 0x4&gt;;
	mediatek,portmap = "wllll";
};

&wmac {
	ralink,mtd-eeprom = &lt;&factory 0&gt;;
};

&sdhci {
	status = "okay";
};

&ehci {
	status = "okay";
};

&ohci {
	status = "okay";
};

&pcie {
	status = "okay";

	compatible = "ralink,mt7620a-pci";
		reg = &lt;0x10140000 0x100
			0x10142000 0x100&gt;;

		resets = &lt;&rstctrl 26&gt;;
		reset-names = "pcie0";

		interrupt-parent = &lt;&cpuintc&gt;;
		interrupts = &lt;4&gt;;
};


</pre>

最后编译的时候，选择

<pre class="lang:sh decode:true " >git clone https://git.lede-project.org/source.git
git fetch --tags
git tag -l
git checkout v17.01.0</pre>

参考：  
1.http://lists.infradead.org/pipermail/lede-commits/2016-September/000876.html  
2.https://lists.openwrt.org/pipermail/openwrt-devel/2015-March/032268.html  
3.http://lxr.free-electrons.com/source/drivers/net/usb/qmi_wwan.c