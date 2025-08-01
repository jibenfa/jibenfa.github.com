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
certbot renew --dry-run
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
           proxy_pass http://127.0.0.1:23456;
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
  #这个配置项是结合chinadns使用的
  "inbound": {
    "protocol": "dokodemo-door",
    "listen":"0.0.0.0",
    "port": 5353,
    "settings": {
      "address": "8.8.8.8",
      "port": 53,
      "network": "udp",
      "timeout": 0,
      "followRedirect": false
    }
  },
  "inboundDetour": [
    {
       "domainOverride": [
        "http",
        "tls"
      ],
      "protocol": "dokodemo-door",
      "port": 1080,
      "listen":"0.0.0.0",
      
      "settings": {
        "network": "tcp",
        "timeout": 30,
        "followRedirect": true
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "vmess",
      "tag": "proxy",
      "settings": {
        "vnext": [
          {
            "address": "你的网址",
            "port": 443,
            "users": [
              {
                "id": "你的key",
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
  ],
  "outboundDetour": [
    {
      "protocol": "freedom",
      "settings": {},
      "tag": "direct"
    }
  ],
  
  "routing": {
    "strategy": "rules",
    "settings": {
      "domainStrategy": "IPIfNonMatch",
      "rules": [
          {
           "type": "field",
           "ip": [
             "8.8.8.8/32",
             "8.8.4.4/32",
             "91.108.56.0/22",
             "91.108.4.0/22",
             "109.239.140.0/24",
             "149.154.164.0/22",
             "91.108.56.0/23",
             "67.198.55.0/24",
             "149.154.168.0/22",
             "149.154.172.0/22"
           ],
           "outboundTag": "proxy"
         },
         {
          "type": "field",
          "domain": [
            "googleapis.cn",
            "google.cn",
            "googleapis",
            "google",
            "domain:facebook.com",
            "domain:github.com",
            "domain:githubusercontent.com",
            "youtube",
            "twitter",
            "instagram",
            "gmail",
            "v2ray.com",
            "github.io",
            "domain:twimg.com",
            "domain:t.co"
          ],
          "outboundTag": "proxy"
        },
        {
           "type": "field",           
           "domain": [
                "ext:h2y.dat:gfw"   #这个文件可以从https://github.com/ToutyRater/V2Ray-SiteDAT/tree/master/geofiles下载
           ],
           "outboundTag": "proxy"
        },
        {
          "type": "field",
          "domain": [
            "geosite:cn",
            "domain:你的网址"
          ],
          "outboundTag": "direct"
        },
        {
          "type": "field",
          "ip": [
            "0.0.0.0/8",
            "10.0.0.0/8",
            "100.64.0.0/10",
            "127.0.0.0/8",
            "169.254.0.0/16",
            "172.16.0.0/12",
            "192.0.0.0/24",
            "192.0.2.0/24",
            "192.168.0.0/16",
            "198.18.0.0/15",
            "198.51.100.0/24",
            "203.0.113.0/24",
            "::1/128",
            "fc00::/7",
            "fe80::/10",
            "geoip:cn"
          ],
          "outboundTag": "direct"
        }
      ]
    }
  },
   "transport": {
    "tcpSettings": {
      "connectionReuse": true
    }
  }
}
</pre>

五、openwrt上配置防火墙

参考上一篇文章
<a href="https://wallsee.org/2019/06/09/v2raye59ca8openwrte4b88be79a84e5ae89e8a385e983a8e7bdb2.html">配置</a>


参考资料：

1).https://certbot.eff.org/lets-encrypt/ubuntubionic-nginx

2).https://zorz.cc/post/v2ray-cdn.html
