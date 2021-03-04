import json
import os
import pickle
import random
import re
import time
import traceback

import demjson
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from domain.OrderItem import OrderItem
from tools.log import logger
from messager.EmailSender import send_email
from tools.util import (
    check_login,
    get_random_useragent
)

chromeDriverPath = "./data/drivers/chromedriver"


class JDMobileSession(object):
    def __init__(self):
        self.user_agent = get_random_useragent()
        # 打开浏览器获取cookie
        self.jdloginURL = "https://plogin.m.jd.com/login/login?"
        self.browser = None

        self.sess = requests.Session()
        self.username = ""
        self.nick_name = ""
        self.is_login = False

        # 购物车信息
        self.cart = {}

        # 下单需要的信息
        self.submitOrderExtraData = {}

    def __openBrowser(self):
        # 打开首页
        self.browser.get(self.jdloginURL)
        logger.info("打开浏览器")

    def __closeBrowser(self):
        self.browser.close()
        logger.info("关闭浏览器")

    def load_cookies(self):
        cookies_file = None
        for name in os.listdir('./data/cookies'):
            if name.endswith('.cookies') and name.startswith(self.username):
                cookies_file = './data/cookies/{0}'.format(name)
                break
        if not cookies_file:
            return
        with open(cookies_file, 'rb') as f:
            local_cookies = pickle.load(f)
        self.sess.cookies.update(local_cookies)
        self.is_login = self._validate_cookies()

    def _save_cookies(self):
        cookies_file = './data/cookies/{0}.cookies'.format(self.username)
        directory = os.path.dirname(cookies_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.sess.cookies, f)

    def _validate_cookies(self):
        """验证cookies是否有效（是否登陆）
        :return: cookies是否有效 True/False
        """
        url = 'https://wq.jd.com/user_redpoint/QueryUserRedPoint?type=4&sceneid=2'
        try:
            resp = self.sess.get(url=url, allow_redirects=False)
            resp_json = json.loads(resp.text)
            if resp_json.get("msg", None) == "success":
                return True
        except Exception as e:
            logger.error(e)
        self.sess = requests.session()
        return False

    def login(self):

        if self.is_login:
            logger.info('登录成功')
            return

        # 打开chrome 浏览器
        self.browser = webdriver.Chrome(chromeDriverPath)
        self.__openBrowser()
        # 等待登录按钮加载
        logger.info(f"请尽快登录")
        WebDriverWait(self.browser, 300).until(
            EC.presence_of_element_located((By.ID, "msShortcutMenu"))
        )
        self.browser.find_element_by_id("msShortcutMenu").click()
        try:
            WebDriverWait(self.browser, 300).until(
                EC.presence_of_element_located((By.CLASS_NAME, "my_header_name"))
            )
            # 加载昵称
            userName = self.browser.find_element_by_class_name("my_header_name")
            logger.info(userName.text)

            self.is_login = True
            logger.info("登录成功")

            cookie_list = self.browser.get_cookies()
            for cookie in cookie_list:
                self.sess.cookies.update({cookie["name"]: cookie["value"]})
            self._save_cookies()
            return True
        #
        except Exception as e:
            # 出错退出
            import traceback
            logger.error(e)
            logger.error(traceback.format_exc())
            return False
        finally:
            self.__closeBrowser()

    def _parse_cart(self, cart: dict):
        # logger.info("购物车共计%d件" % int(cart.get("mainSkuCount")))
        count = 0
        venderCart = cart.get("venderCart")
        cart_detail = {}

        def _parse_product(products):
            _count = 0
            for product in products:
                _count += 1
                mainSku = product.get("mainSku")
                sku_id = mainSku.get("id")
                cart_detail[sku_id] = {
                    'name': mainSku.get("name"),  # 商品名称
                    'vendor_id': vender.get("popInfo").get("vid"),  # 商家id
                    'count': int(mainSku.get("num")),  # 数量
                    'checkType': int(product.get("checkType"))  # 商品选择按钮 预约状态显示为3 正常为0
                }
                cart_detail[sku_id]['selectPromotion'] = "0"
                if product.get("selectPromotion"):
                    for promo in product.get("selectPromotion"):
                        cart_detail[sku_id]['selectPromotion'] = promo.get("pid", "0")
                        break
            return _count

        for vender in venderCart:
            count += _parse_product(vender.get("products"))
            for _item in vender.get("mfsuits"):
                count += _parse_product(_item.get("products"))
            for _item in vender.get("mzsuits"):
                count += _parse_product(_item.get("products"))
        self.cart.clear()
        self.cart.update(cart_detail)
        # logger.info("共计解析到%d件" % count)
        return cart_detail

    @check_login
    def get_cart_detail(self):
        """获取购物车商品详情
        通过网页h5 获取购物车
        :return: 购物车商品信息 dict
        """
        """获取购物车商品详情
                :return: 购物车商品信息 dict
                """
        logger.info(f"获取{self.username}购物车详情")
        url = "https://wq.jd.com/deal/mshopcart/checkcmdy"
        # 选择item提交
        payload = {
            "commlist": "1,,1,1,1,,0"
        }

        headers = {
            'User-Agent': self.user_agent,
            "Origin": "https://p.m.jd.com",
            "Referer": "https://p.m.jd.com/"
        }
        res = self.sess.post(url, data=payload, headers=headers)
        if res.json().get("errId", None) == "0":
            cart = res.json().get("cart")
            cart_detail = self._parse_cart(cart)
            # logger.info(cart_detail)
            return cart_detail
        logger.error(res.json().get("errMsg"))
        logger.error("失败")
        logger.error(res.content.decode("utf8"))
        return None

    @check_login
    def add_item_to_cart(self, orderItem: OrderItem):
        """
        添加商品到购物车
       重要：
       1.商品添加到购物车后将会自动被勾选✓中。
       2.在提交订单时会对勾选的商品进行结算。
       3.部分商品（如预售、下架等）无法添加到购物车

       京东购物车可容纳的最大商品种数约为118-120种，超过数量会加入购物车失败。

       :param orderItems:商品数据对象
       :return:
       """
        url = 'https://wq.jd.com/deal/mshopcart/addcmdy'
        headers = {
            'User-Agent': self.user_agent,
        }
        payload = {
            "commlist": f"{orderItem.pid},,{orderItem.count},{orderItem.pid},1,,0"

        }
        resp = self.sess.get(url=url, params=payload, headers=headers)

        if resp.status_code == requests.codes.OK:
            try:
                if resp.json().get("errId", None) == "0":
                    logger.info('%s x %s 已成功加入购物车', orderItem.pid, orderItem.count)
                    return True
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
            logger.error(resp.json().get("errMsg"))
        logger.error('%s 添加到购物车失败', orderItem.pid)
        logger.error(resp.content.decode("utf8"))
        return False

    @check_login
    def select_item_in_cart(self, orderItem: OrderItem):
        """
        在购物车选中候选商品
        :param orderItem: 候选商品
        :return:
        """
        logger.info(f'{time.ctime()} > 选择商品:{orderItem.pid}【{orderItem.pname}】x {orderItem.count}')
        url = "https://wq.jd.com/deal/mshopcart/checkcmdy"
        # 选择item提交
        payload = {
            "commlist": f"{orderItem.pid},,{orderItem.count},,1,,0"
        }

        headers = {
            'User-Agent': self.user_agent,
            "Origin": "https://p.m.jd.com",
            "Referer": "https://p.m.jd.com/"
        }

        res = self.sess.post(url, data=payload, headers=headers)

        if res.status_code == requests.codes.OK:
            try:
                if res.json().get("errId", None) == "0":
                    logger.info("选择成功")
                    return True
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
            logger.error(res.json().get("errMsg"))
        logger.error("选择失败")
        logger.error(res.content.decode("utf8"))
        return False

    @check_login
    def cancel_select_all_in_cart(self):
        """取消勾选购物车中的所有商品
        :return: 取消勾选结果 True/False
        """
        logger.info(f'{time.ctime()} > 取消选择全部商品')
        url = "https://wq.jd.com/deal/mshopcart/uncheckcmdy"
        # 选择item提交
        payload = {
            "commlist": "",
            "all": 1
        }

        headers = {
            'User-Agent': self.user_agent,
            "Origin": "https://p.m.jd.com",
            "Referer": "https://p.m.jd.com/"
        }

        res = self.sess.post(url, data=payload, headers=headers)

        if res.status_code == requests.codes.OK:
            try:
                if res.json().get("errId", None) == "0":
                    logger.info("取消全部选择成功")
                    return True
                logger.error(res.json().get("errMsg"))
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())

        logger.error("失败")
        logger.error(res.content.decode("utf8"))
        return False

    @check_login
    def change_item_count_in_cart(self, orderItem: OrderItem):
        """修改购物车商品的数量
        修改购物车中商品数量后，该商品将会被自动勾选上。

        :param orderItem:商品数据对象
        :return: 商品数量修改结果 True/False
        """
        url = "https://wq.jd.com/deal/mshopcart/modifycmdynum"
        # 选择item提交
        payload = {
            "commlist": f"{orderItem.pid},,{orderItem.count},{orderItem.pid},11,{orderItem.selectPromotion},0"
        }

        headers = {
            'User-Agent': self.user_agent,
            "Origin": "https://p.m.jd.com",
            "Referer": "https://p.m.jd.com/"
        }

        res = self.sess.get(url, params=payload, headers=headers)

        if res.status_code == requests.codes.OK:
            try:
                if res.json().get("errId", None) == "0":
                    logger.info("修改商品 %s 数量为 %s 成功", orderItem.pid, orderItem.count)
                    return True
                logger.error(res.json().get("errMsg"))
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
        return False

    @check_login
    def confirmOrderItems(self, orderItems: list):
        """
        直接提交订单

        :param orderItem:商品数据对象
        :return: 商品数量修改结果 True/False
        """
        # TODO: 这是页面的访问 找到json的请求接口
        url = "https://wq.jd.com/deal/confirmorder/main"
        commlist = []
        for orderItem in orderItems:
            comm = f"{orderItem.pid},,{orderItem.count},{orderItem.pid},{orderItem.selectPromotion},,0"
            commlist.append(comm)

        print(commlist)

        # 选择item提交
        payload = {
            "commlist": '$'.join(commlist),
            "cu": "true",
            "utm_source": "kong",
            "utm_medium": "jingfen",
            "utm_campaign": "t_1002950757_"
        }

        headers = {
            'User-Agent': self.user_agent,
            "Origin": "https://p.m.jd.com",
            "Referer": "https://p.m.jd.com/"
        }
        logger.debug("1")
        resp = self.sess.get(url, params=payload, headers=headers)
        logger.debug("2")
        try:

            pattern = re.compile(r"\"order\":(.*),\s+\"orderPromotion", re.MULTILINE | re.DOTALL)
            # dealData = pattern.search(resp.text).group(1)
            try:
                dealData = demjson.decode(str(pattern.search(resp.text).group(1)))
            except Exception as e:
                return
            venderCart = dealData.get("venderCart")
            self.submitOrderExtraData["traceId"] = dealData.get("traceId")
            self.submitOrderExtraData["token2"] = dealData.get("token2")
            self.submitOrderExtraData["skulist"] = dealData.get("skulist")

            flag = True

            def _parse_product(products):
                for product in products:
                    mainSku = product.get("mainSku")

                    if int(product.get("mainSku").get("outOfStock")) == 0:
                        continue
                    else:
                        sku_id = mainSku.get("id")
                        sku_name = mainSku.get("name")
                        logger.error(f"订单中{sku_id}:{sku_name}无货！")
                        return False
                return True

            for vender in venderCart:
                if vender.get("products"):
                    flag = _parse_product(vender.get("products")) and flag
                if vender.get("mfsuits"):
                    for _item in vender.get("mfsuits"):
                        flag = _parse_product(_item.get("products")) and flag
                if vender.get("mzsuits"):
                    for _item in vender.get("mzsuits"):
                        flag += _parse_product(_item.get("products")) and flag
            if flag:
                logger.debug("3")
                logger.info("选择Order成功")
                return True
        except Exception as e:
            logger.error(traceback.format_exc())
        logger.debug("3")
        logger.error("选择Order失败")
        return False

    @check_login
    def user_asset(self, orderItems: list):
        """
        提交订单
        :return:
        """
        url = "https://wq.jd.com/deal/masset/userasset"

        skunum = []
        for orderItem in orderItems:
            comm = f"{orderItem.pid}_{orderItem.count}"
            skunum.append(comm)

        data = {
            "reg": 1,
            "action": 0,
            "giftcardtype": 1,
            "isnew": 1,
            "skunum": '|'.join(skunum),
        }
        headers = {
            'User-Agent': self.user_agent,
            "Origin": "https://p.m.jd.com",
            "Referer": "https://p.m.jd.com/"
        }

        res = self.sess.get(url, params=data, headers=headers)

        if res.status_code == requests.codes.OK:
            try:
                res_json = demjson.decode(res.text)
                if res_json.get("errId", None) == "0":
                    logger.info("获取Coupon信息成功")
                    return True
                logger.error(res_json.get("errMsg"))
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())

        logger.error("获取Coupon信息失败")
        return False

    @check_login
    def submitOrder(self):
        """
        提交订单
        :return:
        """
        url = "https://wq.jd.com/deal/msubmit/confirm"
        data = {
            "paytype": 0,
            "paychannel": 1,
            "action": 1,
            "reg": 1,
            "type": 0,
            # TODO:
            "token2": self.submitOrderExtraData.get("token2"),
            "dpid": "",
            "skulist": self.submitOrderExtraData.get("skulist"),
            "scan_orig": "",
            "gpolicy": "",
            "platprice": 0,
            "pick": "",
            "savepayship": 0,
            "sceneval": 2,
            "setdefcoupon": 0,
            "mix": 0,
            "r": random.random(),
            "traceid": self.submitOrderExtraData.get("traceid"),
        }
        headers = {
            'User-Agent': self.user_agent,
            "Origin": "https://p.m.jd.com",
            "Referer": "https://p.m.jd.com/"
        }

        res = self.sess.get(url, params=data, headers=headers)

        if res.status_code == requests.codes.OK:
            try:
                res_json = demjson.decode(res.text)
                if res_json.get("errId", None) == "0":
                    order_id = res_json.get("dealId")
                    price = int(res_json.get("totalPrice")) / 100
                    logger.info("提交Order成功")
                    logger.info(f"下单成功, 订单号：{order_id}, 请前往京东官方商城付款. 需付款: {price}")
                    send_email('下单成功', f'订单号：{order_id}, 请前往京东官方商城付款. 需付款: f{price}')
                    return True
                logger.error(res_json.__str__())
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
            finally:
                # 订单执行成功与否都要等待一段时间 京东风控
                # logger.info("京东风控，等待4s下单")
                # time.sleep(4)
                pass
        logger.error("提交Order失败")
        return False

    @check_login
    def implement_order(self, orderItems: list):
        """
        下单
        :param orderItems:
        :return:
        """
        if self.confirmOrderItems(orderItems):
            if self.submitOrder():
                logger.info("提交订单成功，结束单次任务！")
                return True
        logger.error("提交订单失败，结束单次执行任务！")
        return False

    @check_login
    def cancelOrder(self, orderId):
        """
        取消订单
        :param orderId:
        :return:
        """
        url = "https://wq.jd.com/ordercancel/cancelorder"

        payload = {
            "orderid": f"{orderId}",
            "cancelReason":	"1100",
        }
        headers = {
            'User-Agent': self.user_agent,
            "Referer": "https://wqs.jd.com/"
        }

        res = self.sess.get(url, params=payload, headers=headers)

        if res.status_code == requests.codes.OK:
            try:
                res_json = demjson.decode(res.text)
                if str(res_json.get("retcode", None)) == "0":
                    order_id = res_json.get("data").get("orderid")
                    logger.info(f"取消订单成功！订单号：{order_id}")
                    return True
                logger.error(res_json.get("errMsg"))
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())
        time.sleep(4)
        logger.error("提交Order失败")
        return False
