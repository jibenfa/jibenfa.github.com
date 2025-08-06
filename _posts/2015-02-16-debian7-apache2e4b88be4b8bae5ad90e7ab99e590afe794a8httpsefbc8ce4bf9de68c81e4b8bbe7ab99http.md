---
id: 143
title: Debian 7 Apache2下为子站启用HTTPS，保持主站HTTP
date: 2015-02-16 23:28:12+00:00
author: coffeecat
layout: post
categories:
- linux
tags:
- linux
---
其实不难，简单来说，只要三步即可。。。

# 1.apache2启用ssl

<pre><code class="language-sh">a2enmod ssl</code></pre>

# 2.修改apache配置文件

注：这里使用dovecot ssl生成的  
公钥证书：/etc/dovecot/dovecot.pem  
私钥：/etc/dovecot/private/dovecot.pem  
自签名证书一般不会得到认证，所以浏览器访问时会提示证书非 法，是红色的。  
如果要显示为绿色，可以考虑向某些组织申请ssl证书，有收费和免费的。

<pre><code class="language-sh">vi /etc/apache2/sites-enabled/example.com.conf</code></pre>

内容如下（这种方法感觉挺笨的，但是有效。。）：  
<!--more-->

<pre><code class="language-vim"># domain: example.com
# public: /var/www/example.com/public_html/

NameVirtualHost *:443  
&lt;VirtualHost *:80&gt;
ServerName <strong>ip地址</strong>
&lt;Location /&gt;
Order Allow,Deny
Deny from all
&lt;/Location&gt;
&lt;/VirtualHost&gt;

&lt;VirtualHost *:80&gt;
  # Admin email, Server Name (domain name), and any aliases
  ServerAdmin webmaster@example.com
  ServerName  www.example.com
  ServerAlias example.com
  # Index file and Document Root (where the public files are located)
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html
  # Log file locations
  LogLevel warn
  ErrorLog  /var/www/example.com/log/error.log
  CustomLog /var/www/example.com/log/access.log combined
&lt;/VirtualHost&gt;
  
&lt;Directory /var/www/example.com/public_html/postfixadmin&gt;
  RewriteEngine on
  RewriteCond %{SERVER_PORT} !^443$
  RewriteRule ^(.*)?$ https://pfadmin.example.com/$1 [L,R]
&lt;/Directory&gt;

&lt;VirtualHost *:443&gt;
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/postfixadmin
  ServerName pfadmin.example.com:443
  ServerAlias pfadmin.example.com
  SSLEngine On
  SSLOptions +StrictRequire
  SSLCertificateFile /etc/dovecot/dovecot.pem
  SSLCertificateKeyFile /etc/dovecot/private/dovecot.pem
&lt;/VirtualHost&gt;

&lt;VirtualHost *:80&gt;
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/postfixadmin
  ServerName pfadmin.example.com
&lt;/VirtualHost&gt;

&lt;Directory /var/www/example.com/public_html/webmail&gt;
  Options FollowSymLinks
  &lt;IfModule mod_php5.c&gt;
    php_flag register_globals off
  &lt;/IfModule&gt;
  &lt;IfModule mod_dir.c&gt;
    DirectoryIndex index.php
  &lt;/IfModule&gt;
  RewriteEngine on
  RewriteCond %{SERVER_PORT} !^443$
  RewriteRule ^(.*)?$ https://webmail.example.com/$1 [L,R]
&lt;/Directory&gt;

&lt;Directory /var/www/example.com/public_html/webmail/data&gt;
 deny from all
&lt;/Directory&gt;

&lt;VirtualHost *:443&gt;
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/webmail
  ServerName webmail.example.com:443
  ServerAlias webmail.example.com
  SSLEngine On
  SSLOptions +StrictRequire
  SSLCertificateFile /etc/dovecot/dovecot.pem
  SSLCertificateKeyFile /etc/dovecot/private/dovecot.pem
&lt;/VirtualHost&gt;

&lt;VirtualHost *:80&gt;
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/webmail
  ServerName webmail.example.com
&lt;/VirtualHost&gt;</code></pre>

# 3.重启apache2服务

<pre><code class="language-sh">service apache2 restart</code></pre>

避免重启时apache因证书密码卡住无法ssh  
需将加密的key文件解密。。。

<pre><code class="language-sh">openssl rsa -in key.pem -out newkey.pem</code></pre>