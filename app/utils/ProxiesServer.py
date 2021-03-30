import datetime
import json
import random

import requests


class ProxiesServer(object):
    """
    随机生成proxy调用
    """
    def __init__(self):
        self.IPPOOL = list()
        self.IPPOOLTIMESTAMP = datetime.datetime.now()
        self.apiUrl = "http://ip.16yun.cn:817/myip/pl/eaec029c-b654-48d1-a7b0-dd690df69303/?s=qcjismgkdi&u=cycmay&format=json"
        self.get_proxies_from_api()


    def get_proxies_from_api(self):
        # 获取IP列表
        try:
            ip_list = list(json.loads(requests.get(self.apiUrl).text).get("proxy"))
            # print(ip_list)
            if not len(ip_list) == 0:
                self.IPPOOL.clear()
                self.IPPOOLTIMESTAMP = datetime.datetime.now()
                for ip in ip_list:
                    self.IPPOOL.append({
                        "http": f"http://{ip.get('ip')}:{ip.get('port')}",
                        "https": f"https://{ip.get('ip')}:{ip.get('port')}",
                    })
            print(self.IPPOOL)
        except Exception as e:
            pass

    def get_proxies_from_api2(self):
        # 代理服务器(产品官网 www.16yun.cn)
        proxyHost = "u6068.10.tn.16yun.cn"
        proxyPort = "6442"

        # 代理验证信息
        proxyUser = "16MTQXHX"
        proxyPass = "894839"

        proxyMeta = "http://%(user)s:%(pass)s@%(host)s:%(port)s" % {
            "host": proxyHost,
            "port": proxyPort,
            "user": proxyUser,
            "pass": proxyPass,
        }

        # 设置 http和https访问都是用HTTP代理
        proxies = {
            "http": proxyMeta,
            "https": proxyMeta,
        }

        return proxies

    def get_random_proxy(self):
        """ 随机从ip数据库中读取proxy"""
        # print(self.IPPOOL)

        now_time = datetime.datetime.now()
        # 更新api proxy
        if (now_time - self.IPPOOLTIMESTAMP).seconds > 60 * 2:
            self.get_proxies_from_api()

        return random.choice(self.IPPOOL)
