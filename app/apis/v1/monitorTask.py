import datetime
import json
import re
import time

from bs4 import BeautifulSoup
from bson import ObjectId
from flask import request, jsonify, current_app
from flask.views import MethodView

from flask_restful import abort

from app.apis.v1 import api_v1
from app.apis.v1.schemas import buyitems_schema, duProducts_schema
from app.domain.MongoSession import MongoSession
from app.domain.RedisSession import RedisSession
from app.extensions import api_config
from app.models import Buyitem, du_product

from app.extensions import db

import requests

class ManageStocksAPI(MethodView):
    """
    管理监控pids stocks
    """
    _redis = RedisSession()
    _redis_skuIds_key = "JDSkuIds:"

    def post(self):
        method = request.get_json().get("method")
        if not method:
            abort(400)
        else:
            ret = {"code": 200}
            params = request.get_json().get("params")
            if method == "addSkuIds":
                #     向redis的监测hash表中增加skuIds
                skuIds = params["skuIds"]
                for skuId in skuIds:
                    self._redis.sAdd(self._redis_skuIds_key, str(skuId))
            elif method == "rmSkuId":
                skuId = params["skuId"]
                self._redis.sRemove(self._redis_skuIds_key, skuId)
            elif method == "rmSkuIds":
                skuIds = params["skuIds"]
                for skuId in skuIds:
                    self._redis.sRemove(self._redis_skuIds_key, skuId)
            elif method == "rmSkuIdsAll":
                skuIds = self._redis.sList(self._redis_skuIds_key)
                for skuid in skuIds:
                    self._redis.sRemove(self._redis_skuIds_key, skuid)

            elif method == "getSkuIds":
                skuIds = self._redis.sList(self._redis_skuIds_key)
                data = []
                for skuid in skuIds:
                    data.append(skuid)
                ret["data"] = data
            return ret

class ManageTasksAPI(MethodView):
    """
    管理监控的任务列表
    """
    _mongo = MongoSession(db="Gaze", col="JDTask")
    _redis = RedisSession()
    _redis_skuIds_key = "JDSkuIds:"

    def post(self):
        method = request.get_json().get("method")
        if not method:
            abort(400)
        else:
            ret = {"code": 200}
            params = request.get_json().get("params")
            _id = params.get("_id")
            task = params.get("task")
            name = params.get("name")
            if method == "addTask":
                # 加入任务列表
                params.pop("_id")
                self._mongo.create(params)

                # redis中加入pids
                for entry in task:
                    pid = entry.get("pid")
                    for skuId in pid:
                        self._redis.sAdd(self._redis_skuIds_key, str(skuId))
                    ret["message"] = f"添加任务成功！"
            elif method == "updateTask":
                where = {}
                params.pop("_id")
                where["_id"] = ObjectId(_id)
                self._mongo.update(where, {'$set': params})
                ret["message"] = f"修改任务{_id}成功！"
            elif method == "removeTask":
                where = {}
                where["_id"] = ObjectId(_id)
                self._mongo.delete(where)
                ret["message"] = f"删除任务{_id}成功！"
            elif method == "removeTasksAll":
                # 执行一次事务
                @self._mongo.transaction
                def remove():
                    for item in self._mongo.read():
                        item["_id"] = str(item["_id"])
                        self._mongo.delete({"_id": ObjectId(item["_id"])})
                remove()
                ret["message"] = f"删除所有任务成功！"
            elif method == "listTasks":
                tasks = []
                for item in self._mongo.read():
                    item["_id"] = str(item["_id"])
                    tasks.append(item)
                ret["tasks"] = tasks

            return ret

class ManageHistroyTasksAPI(MethodView):
    """
    管理监控的历史任务列表
    """
    _mongoHistory = MongoSession(db="Gaze", col="JDTaskHistory")
    def post(self):
        method = request.get_json().get("method")
        if not method:
            abort(400)
        else:
            ret = {"code": 200}
            params = request.get_json().get("params")
            _id = params.get("_id")
            task = params.get("task")
            name = params.get("name")
            if method == "addTask":
                # 加入任务列表
                params.pop("_id")
                # 历史记录增加 并加入时间戳
                params["time"] = int(datetime.datetime.now().timestamp() * 1000)
                self._mongoHistory.create(params)

                ret["message"] = f"添加历史任务成功！"
            elif method == "removeTask":
                where = {}
                where["_id"] = ObjectId(_id)
                self._mongoHistory.delete(where)
                ret["message"] = f"删除历史任务{_id}成功！"
            elif method == "removeTasksAll":
                # 执行一次事务
                @self._mongo.transaction
                def remove():
                    for item in self._mongo.read():
                        item["_id"] = str(item["_id"])
                        self._mongoHistory.delete({"_id": ObjectId(item["_id"])})
                remove()
                ret["message"] = f"删除所有历史任务成功！"
            elif method == "listTasks":
                tasks = []
                for item in self._mongoHistory.read().sort("time", -1):
                    item["_id"] = str(item["_id"])
                    tasks.append(item)
                ret["tasks"] = tasks

            return ret




class GetParsePromoteUrlAPI(MethodView):
    """
    通过解析推广的URL得到目标产品的所有pid-tip map
    """
    def post(self):
        targetUrl = request.get_json().get("targetUrl")
        ret = {
            "code": 200,
            "data": self.parse_promote_url(targetUrl)
        }
        return jsonify(ret)


    def parse_promote_url(self, url):
        """
        解析推广的网页信息
        :param url:
        :return:
        """

        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.20 Safari/537.36",
            "referer": "https://u.jd.com/",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-site",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1"
        }
        resp = requests.get(url=url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        pattern = re.compile(r"var pageConfig = {(.*?)};$", re.MULTILINE | re.DOTALL)
        script = soup.find("script", text=pattern)
        pageConfig = str(pattern.search(script.string).group(1))
        venderId = re.search("venderId:(\d*),", pageConfig, re.S).group(1)
        skuid = re.search("skuid: (\d*),", pageConfig, re.S).group(1)
        # href: '//item.jd.com/10022768846633.html',
        href = "https:" + re.search("href: \'(.*?)\',", pageConfig, re.S).group(1)
        # src: 'jfs/t1/157714/40/4211/172119/6007bfc7E01eecf62/b9cc74f0ec5a9ea9.jpg',
        imgUrl = "https://img13.360buyimg.com/n1/" + re.search("src: \'(.*?)\',", pageConfig, re.S).group(1)
        shopId = re.search("shopId:\'(\d*)\',", pageConfig, re.S).group(1)
        title = re.search("name: \'(.*?)\',", pageConfig, re.S).group(1)
        try:
            # 五位六位或者八位的数字货号
            if re.search("(\d{5,8}\-\d{3})", title, re.S):
                articleNumber = re.search("(\d{5,8}\-\d{3})", title, re.S).group()
            elif re.search("(\d{6,8})", title, re.S):
                articleNumber = re.search("(\d{6,8})", title, re.S).group()
            # 两位字母+四位数字货号
            elif re.search("([A-Z]{1,2}\d{4,5}\-\d{3})", title, re.S):
                articleNumber = re.search("([A-Z]{1,2}\d{4,5}\-\d{3})", title, re.S).group()
            elif re.search("([A-Z]{1,2}\d{4,5})", title, re.S):
                articleNumber = re.search("([A-Z]{1,2}\d{4,5})", title, re.S).group()
            # 斯凯奇 四-五位数字加三-五位字母
            elif re.search("(\d{4,5}[A-Z]{3,5})", title, re.S):
                articleNumber = re.search("(\d{4,5}[A-Z]{3,5})", title, re.S).group()
            # 李宁 四位字母加三位数字
            else:
                articleNumber = "error"
        except Exception as e:
            articleNumber = "error"

        ret = {}
        ret["title"] = f"[{articleNumber}]{title}"
        ret["pid_tip_map"] = []
        ret["href"] = href
        ret["imgUrl"] = imgUrl

        if re.search("colorSize: (.*?\])", pageConfig, re.S):
            colorSize = json.loads(re.search("colorSize: (.*?\])", pageConfig, re.S).group(1))
            for item in colorSize:
                newer = {}
                newer["pid"] = str(item.get("skuId"))
                newer["tip"] = item.get("尺码", "None") + " " +item.get("颜色", "None")
                ret["pid_tip_map"].append(newer)
        else:
            # 没有colorsize 则为单品
            newer = {}
            newer["pid"] = skuid
            newer["tip"] = "单品"
            ret["pid_tip_map"].append(newer)

        return ret


api_v1.add_url_rule('/JDtask/manageStocks', view_func=ManageStocksAPI.as_view('api_JDtaskManageStocks'), methods=["POST"])
api_v1.add_url_rule('/JDtask/manageTasks', view_func=ManageTasksAPI.as_view('api_JDtaskManageTasks'), methods=["POST"])
api_v1.add_url_rule('/JDtask/manageHistoryTasks', view_func=ManageHistroyTasksAPI.as_view('api_JDtaskManageHistoryTasks'), methods=["POST"])
api_v1.add_url_rule('/JDtask/getParsePromoteUrl', view_func=GetParsePromoteUrlAPI.as_view('api_JDtaskGetParsePromoteUrl'), methods=["POST"])
