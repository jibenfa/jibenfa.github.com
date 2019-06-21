---
id: 662
title: v2ray+LetsEncrypt+cdn部署
date: 2019-06-14T14:46:57+00:00
author: coffeecat
layout: post




categories:


---
为了拯救被墙的ip，参考了一些资料，最终实现了v2ray+LetsEncrypt+cdn部署。
首先是申请一个域名，example.com

一、vps部署Nginx和LetsEncrypt

<pre lang="bash" line="0"  colla="+">
apt update
apt install nginx -y
apt-get update
apt-get install software-properties-common
add-apt-repository universe
add-apt-repository ppa：certbot/certbot
apt-get update
apt-get install certbot python-certbot-nginx 
</pre>

自动安装Nginx证书：

<pre lang="bash" line="0"  colla="+">
certbot --nginx
</pre>

然后crontab -e增加计划任务，自动更新https证书

<pre lang="bash" line="0"  colla="+">
certbot --nginx certonly
</pre>

二、vps配置Nginx和安装配置v2ray

设置/etc/nginx/sites-enabled/default为：

<pre lang="bash" line="0"  colla="+">
server {

        #index index.html index.htm index.nginx-debian.html;
        server_name example.com; # managed by Certbot


        location /test
        {
           proxy_redirect off;
           proxy_pass http://127.0.0.1:123456;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $http_host;
        }



    listen [::]:443 ssl ipv6only=on; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    ssl on;

}
</pre>

搞完以后，执行：
<pre lang="bash" line="0"  colla="+">
service nginx restart
</pre>


安装v2ray就不说了，服务端配置文件如下：

<pre lang="bash" line="0"  colla="+">
{
  "inbounds": [
    {
      "port": 123456,
      "listen":"127.0.0.1",
      "protocol": "vmess",
      "settings": {
        "clients": [
          {
            "id": "你的id",
            "alterId": 64
          }
        ]
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
        "path": "/test"
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "settings": {}
    }
  ]
}
</pre>

搞完以后，执行：
<pre lang="bash" line="0"  colla="+">
service v2ray restart
</pre>


三、在cloudflare上配置cdn
不提了，说多泪，主要是:

1)在dns里面，将解析域名example.com指向被墙ip

2)将ns server设置为cloudflare的ns

3）在crypto菜单里面讲ssl设置为full，将“Always Use HTTPS”设置为ON！！！

四、客户端配置v2ray

<pre lang="bash" line="0"  colla="+">
{
  "inbounds": [
    {
      "port": 1080,
      "listen": "127.0.0.1",
      "protocol": "socks",
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      },
      "settings": {
        "auth": "noauth",
        "udp": false
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "vmess",
      "settings": {
        "vnext": [
          {
            "address": "example.com",
            "port": 443,
            "users": [
              {
                "id": "你的id",
                "alterId": 64
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "ws",
        "security": "tls",
        "wsSettings": {
          "path": "/test"
        }
      }
    }
  ]
}
</pre>


参考资料：

1).https://certbot.eff.org/lets-encrypt/ubuntubionic-nginx

2).https://zorz.cc/post/v2ray-cdn.html
