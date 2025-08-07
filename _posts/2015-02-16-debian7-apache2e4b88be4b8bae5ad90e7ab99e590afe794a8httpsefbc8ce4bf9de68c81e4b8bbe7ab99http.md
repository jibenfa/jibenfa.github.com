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

```sh
a2enmod ssl
```

# 2.修改apache配置文件

注：这里使用dovecot ssl生成的  
公钥证书：/etc/dovecot/dovecot.pem  
私钥：/etc/dovecot/private/dovecot.pem  
自签名证书一般不会得到认证，所以浏览器访问时会提示证书非 法，是红色的。  
如果要显示为绿色，可以考虑向某些组织申请ssl证书，有收费和免费的。

```sh
vi /etc/apache2/sites-enabled/example.com.conf
```

内容如下（这种方法感觉挺笨的，但是有效。。）：  
<!--more-->

```vim
# domain: example.com
# public: /var/www/example.com/public_html/

NameVirtualHost *:443  
<VirtualHost *:80>
ServerName <strong>ip地址</strong>
<Location />
Order Allow,Deny
Deny from all
</Location>
</VirtualHost>

<VirtualHost *:80>
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
</VirtualHost>
  
<Directory /var/www/example.com/public_html/postfixadmin>
  RewriteEngine on
  RewriteCond %{SERVER_PORT} !^443$
  RewriteRule ^(.*)?$ https://pfadmin.example.com/$1 [L,R]
</Directory>

<VirtualHost *:443>
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/postfixadmin
  ServerName pfadmin.example.com:443
  ServerAlias pfadmin.example.com
  SSLEngine On
  SSLOptions +StrictRequire
  SSLCertificateFile /etc/dovecot/dovecot.pem
  SSLCertificateKeyFile /etc/dovecot/private/dovecot.pem
</VirtualHost>

<VirtualHost *:80>
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/postfixadmin
  ServerName pfadmin.example.com
</VirtualHost>

<Directory /var/www/example.com/public_html/webmail>
  Options FollowSymLinks
  <IfModule mod_php5.c>
    php_flag register_globals off
  </IfModule>
  <IfModule mod_dir.c>
    DirectoryIndex index.php
  </IfModule>
  RewriteEngine on
  RewriteCond %{SERVER_PORT} !^443$
  RewriteRule ^(.*)?$ https://webmail.example.com/$1 [L,R]
</Directory>

<Directory /var/www/example.com/public_html/webmail/data>
 deny from all
</Directory>

<VirtualHost *:443>
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/webmail
  ServerName webmail.example.com:443
  ServerAlias webmail.example.com
  SSLEngine On
  SSLOptions +StrictRequire
  SSLCertificateFile /etc/dovecot/dovecot.pem
  SSLCertificateKeyFile /etc/dovecot/private/dovecot.pem
</VirtualHost>

<VirtualHost *:80>
  DirectoryIndex index.html index.php
  DocumentRoot /var/www/example.com/public_html/webmail
  ServerName webmail.example.com
</VirtualHost>
```

# 3.重启apache2服务

```sh
service apache2 restart
```

避免重启时apache因证书密码卡住无法ssh  
需将加密的key文件解密。。。

```sh
openssl rsa -in key.pem -out newkey.pem
```