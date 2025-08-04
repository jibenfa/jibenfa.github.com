---
id: 526
title: PC端和Openwrt端的i-Shanghai自动登录研究
date: 2016-03-17 19:06:56+00:00
author: coffeecat
layout: post
categories:
- openwrt
tags:
- openwrt
---
上海有免费的i-Shanghai，速度还不错，唯一麻烦的是每次登录都要通过手机号和用户名密码进行验证。作为组装级的程序猿，如不能做到自动登录是十分痛苦的事情。。。于是，加班之余展开了为期一周的研究。。。最终实现了PC端和Openwrt端的i-Shanghai自动登录。。。。

首先，分析阶段：  
i-Shanghai的wifi连接上以后，任意打开某网页，例如:www.baidu.com，就会自动跳转到如下页面：

<!--more-->

<pre class="lang:vim decode:true " >'https://wlan.ct10000.com/?basetype=3&nasPortId='.$nasPortId.'&UserInputURL=http://www.baidu.com/&nasIp='.$nasIp;</pre>

里面的id和ip估计就是热点的id和ip了。。。

这个页面包含一个框架，实际的登录页面就是在框架里面的，我认为这是基于安全性的考虑，框架的地址，类似：

<pre class="lang:vim decode:true " >'https://wlan.ct10000.com/'.$longString</pre>

直接打开框架地址后，出现了熟悉的登录框，通过分析元素发现，提交的要素有些是hidden的，且最后的提交按钮是调用javascript，经测试直接通过模拟点击是不行了（perl的www::mechanize似乎不支持javascript），这样的设计也是为了安全考虑吧，只有最后一条路——抓包分析了。

最麻烦的是，为了安全考虑，这些网址都是https的，通过wireshark抓包是没有用的，只能通过Fiddler或者chrome的开发者模式抓包，通过抓包，知道了提交的要素和地址：  
提交的内容是：

<pre class="lang:vim decode:true " >paramStr
paramStrEnc
province
prefix
logintype
UserName
PassWord</pre>

提交的地址是：

<pre class="lang:vim decode:true " >https://wlan.ct10000.com/authServlet</pre>

前2个提交内容在框架页面就已经生成了，里面应该包含了热点的id等相关信息，如果提交时不带上或者带错了这些信息，就会提示此处不是热点。。。

其次，剩下的就是编码的活了，PC端可以用perl脚本，Openwrt端不能用perl，因为perl在op上的官方的库不支持https。。。。只好改用python，整个python安装需要7MB的路由器rom空间，也就是说，路由器至少要有16MB的flash，刷完op以后才能装整个python环境。

与pc端的perl脚本相比，op端的python脚本有不少差别，由于op上还要考虑dns的因素，故为了防止无法解析wlan.ct10000.com，需要提前获得其ip地址，另外为了防止与全局ss冲突，还需要在其ignorelist里面加入该ip地址，并且在crontab中设定定时登录任务。。

下面附上PC端i-Shanghai自动登录perl脚本，模拟iPhone登录（python脚本不提供，免得被不法奸商利用）： 

<pre class="lang:perl decode:true " >#/usr/bin/perl -w
    use strict;
    use warnings;
    use WWW::Mechanize; 

    my $username = '13888888888';
    my $pass = '222222';
    my $nasIp = '133.133.133.133'; 
    my $nasPortId = 'lag-1:8888.888';   
    my $url = 'https://wlan.ct10000.com/?basetype=3&nasPortId='.$nasPortId.'&UserInputURL=http://www.baidu.com/&nasIp='.$nasIp;
    
    my $impcontent;
    #打开浏览器
    my $ua = WWW::Mechanize-&gt;new(); 
    $ua-&gt;cookie_jar(HTTP::Cookies-&gt;new()); 
    $ua-&gt;agent_alias('Windows IE 6');
    
    #打开网址
    my $response = $ua-&gt;get($url);
    my $decontent =$response-&gt;decoded_content;
    
    $decontent =~ s/\n//g;
                
   #打开框架网址            
   if($decontent =~ /mainFrame\" src=\"(.*)\" noresize/)
   {
   	 $url = 'https://wlan.ct10000.com'.$1;

   }
    $response = $ua-&gt;get($url);           
    $decontent =$response-&gt;decoded_content; 
    $decontent =~ s/\n/0D0A/g;
    $decontent =~ s/\s//g;
 
    
    #取出框架要素
    my $paramStr='';
    if($decontent =~ /id=\"paramStr\"value=\"(.*)?\"\/&gt;0D0A&lt;inputtype=\"hidden\"name=\"paramStrEnc\"/)  
    {
    	 $paramStr=$1;   	  
    }
    my $paramStrEnc='';
    if($decontent =~ /id=\"paramStrEnc\"value=\"(.*)?\"\/&gt;0D0A&lt;inputtype=\"hidden\"name=\"province\"id=\"province\"/)
    {
    	 $paramStrEnc=$1;
    }
    my $province='telecom.dynamic@ish';
    my $prefix='NE';
    my $logintype='2';
   
    #简易uri编码，不用调用URI::Encode
    $paramStr =~ s/([^^A-Za-z0-9\-_.!~*'()])/ sprintf "%%%02X", ord $1 /eg;
    $paramStr =~ s/0D0A/\%0D\%0A/g;
    $paramStrEnc =~ s/([^^A-Za-z0-9\-_.!~*'()])/ sprintf "%%%02X", ord $1 /eg;
    $province =~ s/([^^A-Za-z0-9\-_.!~*'()])/ sprintf "%%%02X", ord $1 /eg;
    my $location = 'https://wlan.ct10000.com/style/ish_fx/index.jsp?paramStr=' . $paramStr;
    
    my $content =  'paramStr=' . $paramStr . '&paramStrEnc=' . $paramStrEnc  . '&province=' . $province . '&prefix=' . $prefix . '&logintype=' . $logintype . '&UserName=' . $username . '&PassWord=' . $pass;  
    print $content;  
    
    my $url2='https://wlan.ct10000.com/authServlet';
    #发起登陆
    $response =  $ua-&gt;post($url2,              
                        'Accept' =&gt;  'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding' =&gt;  'gzip, deflate',
                        'Accept-Language' =&gt;  'zh-CN,zh;q=0.8',
                        'Cache-Control' =&gt;  'max-age=0',
                        'Connection' =&gt;  'keep-alive',
                        'Content-Length' =&gt;  '1067',
                        'Content-Type' =&gt;  'application/x-www-form-urlencoded',
                        'Cookie' =&gt;  'JSESSIONID=22B2B92222C0F258866778895E2F4450F80',
                        'Host' =&gt;  'wlan.ct10000.com',
                        'Origin' =&gt;  'https://wlan.ct10000.com',
                        'Referer' =&gt;   $location,  
                        'Upgrade-Insecure-Requests' =&gt;  '1',
                        'User-Agent' =&gt;  'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5',
                        'Content' =&gt; $content
                        );
                        
       
   # $decontent = $response-&gt;decoded_content;       
   # print $decontent;
                 </pre>