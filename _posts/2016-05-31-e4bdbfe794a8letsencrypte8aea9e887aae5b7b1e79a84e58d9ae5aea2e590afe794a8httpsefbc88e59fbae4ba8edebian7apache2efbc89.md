---
id: 562
title: 使用lets encrypt让自己的博客启用https（基于debian7+apache2）
date: 2016-05-31 20:04:07+00:00
author: coffeecat
layout: post
categories:
- linux
tags:
- linux
---
之前用过starssl的免费ssl证书，现在到期了，因为申请和续期都很麻烦，所以懒得再弄。最近在网上看到去年底，成立了个新机构（from wiki）：  
Let&#8217;s Encrypt 是一个将于2015年末推出的数字证书认证机构，将通过旨在消除当前手动创建和安装证书的复杂过程的自动化流程，为安全网站提供免费的SSL/TLS证书。 

一是简单，二是免费，为啥不用呢，于是看了看文档，就开始弄了：  
<!--more-->

假如你是example.com 的所有者，只要在server端登录，并执行：

<pre><code class="language-sh">wget https://dl.eff.org/certbot-auto
chmod a+x certbot-auto
./certbot-auto certonly --webroot -w /var/www/example -d example.com -d www.example.com</code></pre>

如果之前域名解析正常可以访问的话，会有如下提示：

<pre><code class="language-vim">IMPORTANT NOTES:
 - Congratulations! Your certificate and chain have been saved at
   /etc/letsencrypt/live/example.com/fullchain.pem. Your cert will
   expire on 2016-08-29. To obtain a new or tweaked version of this
   certificate in the future, simply run certbot-auto again. To
   non-interactively renew *all* of your ceriticates, run
   "certbot-auto renew"
 - If you like Certbot, please consider supporting our work by:

   Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
   Donating to EFF:                    https://eff.org/donate-le</code></pre>

说明证书链和私钥、证书已经产生了。。。

如果失败，则会有类似提示：

<pre><code class="language-vim">Failed authorization procedure. www.example.com (http-01): urn:acme:error:unauthorized :: The client lacks sufficient authorization :: Invalid response from http://www.example.com/.well-known/acme-challenge/OJvVsXKC4odxeV4darP05x4T7-ymOykX0UT6jqh0rees: "&lt;!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN"&gt;
&lt;html&gt;&lt;head&gt;
&lt;title&gt;403 Forbidden&lt;/title&gt;
&lt;/head&gt;&lt;body&gt;
&lt;h1&gt;Forbidden&lt;/h1&gt;
&lt;p"

IMPORTANT NOTES:
 - The following errors were reported by the server:
……</code></pre>

这就需要另外改配置了。。。

然后修改一下apache的配置文件：

<pre><code class="language-vim"># domain: example.com
# public: /var/www/example.com/public_html/

NameVirtualHost *:443  
&lt;VirtualHost *:80&gt;
ServerName ip地址，防止直接ip访问
&lt;Location /&gt;
Order Allow,Deny
Deny from all
&lt;/Location&gt;
&lt;/VirtualHost&gt;



&lt;Directory /var/www/example.com/public_html/&gt;
  &lt;IfModule mod_headers.c&gt; 
        Header always set Strict-Transport-Security "max-age=15553000; includeSubDomains; preload" 
  &lt;/IfModule&gt; 
  RewriteEngine on
  RewriteCond %{SERVER_PORT} !^443$
  RewriteRule ^(.*)?$ https://routeragency.com/$1 [L,R]
&lt;/Directory&gt;


&lt;VirtualHost *:443&gt;
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/
  ServerName routeragency.com:443
  ServerAlias routeragency.com example.com www.routeragency.com
  SSLEngine On
  SSLProtocol ALL -SSLv2 -SSLv3
  SSLHonorCipherOrder on
  SSLCipherSuite ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES256-SHA256:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES256-GCM-SHA384:AES128-GCM-SHA256:AES256-SHA256:AES128-SHA256:AES256-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4
  SSLCompression Off
  SSLOptions +StrictRequire
  SSLCertificateFile  /etc/letsencrypt/live/routeragency.com/fullchain.pem
  SSLCertificateKeyFile /etc/letsencrypt/live/routeragency.com/privkey.pem
  SSLCACertificateFile /etc/letsencrypt/live/routeragency.com/chain.pem
&lt;/VirtualHost&gt;

&lt;VirtualHost *:80&gt;
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/
  ServerName routeragency.com
  ServerAlias www.example.com www.routeragency.com example.com
&lt;/VirtualHost&gt;</code></pre>

然后重启apache服务：

<pre><code class="language-sh">service apache2 restart
</code></pre>

最后在crotab中设置2个月更新一次证书（因为这个机构的证书只有3个月有效期）：

<pre><code class="language-sh">crontab -e
</code></pre>

添加定时任务

<pre><code class="language-sh">0 0 1 */2 * xxx/certbot/certbot-auto renew && /etc/init.d/apache2 restart</code></pre>

搞定，简单吧。。。  
可以到www.ssllabs.com测试一下评级，满足一下虚荣心。。。 

<br>
 <img src="https://jibenfa.github.io/uploads/2016/05/2016053120127.png" width="1000" height="618" alt="AltText" />
 <br>
  
参考资料：  
1.https://letsencrypt.org/getting-started/  
2.https://certbot.eff.org/#debianwheezy-apache  
3.https://ksmx.me/letsencrypt-ssl-https/?utm\_source=v2ex&utm\_medium=forum&utm_campaign=20160529  
4.http://blog.rlove.org/2013/12/strong-ssl-crypto.html