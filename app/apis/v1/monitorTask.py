import datetime
import json
import re
import traceback

import requests
from bs4 import BeautifulSoup
from bson import ObjectId
from flask import request, jsonify
from flask.views import MethodView
from flask_restful import abort

from app.apis.v1 import api_v1
from app.domain.MongoSession import MongoSession
from app.domain.RedisSession import RedisSession
from app.utils.ProxiesServer import ProxiesServer


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


class ManageSolutionsAPI(MethodView):
    """
    管理解决方案
    """
    _mongo_entry = MongoSession(db="Gaze", col="JDEntries")
    _mongo_solutions = MongoSession(db="Gaze", col="JDSolutions")
    _request_json = None

    _redis = RedisSession()
    _redis_skuIds_key = "JDSkuIds:"
    _redis_Solutions_set_key = "JDSolutionsSet:"
    # 保存solution的metadata
    _redis_Solutions_metadata_key = "JDSolutionsMetadata:"
    _redis_Solutions_hash_key = "JDSolutionsHash:"

    def __init__(self):
        self.optional = dict()
        self.init_optional()

    def init_optional(self):
        self.optional = {
            "addSolution": self.addSolution,
            "updateSolution": self.updateSolution,
            "listSolutions": self.listSolutions,
            "removeSolution": self.removeSolution,
            "pauseSolution": self.pauseSolution,
            "recoverSolution": self.recoverSolution
        }

    def addSolution(self):
        ret = {"code": 200}
        params = self._request_json.get("params")
        # 加入任务列表
        params.pop("_id")
        insertedId = str(self._mongo_solutions.create(params))
        ret["message"] = f"添加solution{insertedId}成功！"
        ret["solutionId"] = insertedId
        # redis中集合Solution: 加入该id
        self._redis.sAdd(set_key=self._redis_Solutions_set_key, item=insertedId)
        # redis中加入solution:[id]的配置
        self._redis.hSet(hash_key=self._redis_Solutions_metadata_key + insertedId, key="name",
                         value=str(params.get("name")))
        self._redis.hSet(hash_key=self._redis_Solutions_metadata_key + insertedId, key="target",
                         value=float(params.get("target")))
        self._redis.hSet(hash_key=self._redis_Solutions_metadata_key + insertedId, key="deviation",
                         value=float(params.get("deviation")))
        self._redis.hSet(hash_key=self._redis_Solutions_metadata_key + insertedId, key="id",
                         value=str(insertedId))
        return ret

    def updateSolution(self):
        ret = {"code": 200}
        params = self._request_json.get("params")
        # 只修改以下几部分
        _id = params.get("_id")
        where = {}
        params.pop("_id")
        where["_id"] = ObjectId(_id)

        item = {
            "name": params.get("name"),
            "target": params.get("target"),
            "deviation": params.get("deviation")
        }
        # redis中修改solution:[id]的配置
        self._redis.hSet(hash_key=self._redis_Solutions_metadata_key + _id, key="name",
                         value=str(params.get("name")))
        self._redis.hSet(hash_key=self._redis_Solutions_metadata_key + _id, key="target",
                         value=float(params.get("target")))
        self._redis.hSet(hash_key=self._redis_Solutions_metadata_key + _id, key="deviation",
                         value=float(params.get("deviation")))

        self._mongo_solutions.update(where, {'$set': item})
        ret["message"] = f"修改Solution {_id} 成功！"
        return ret

    def listSolutions(self):
        ret = {"code": 200}
        solutions = []
        for item in self._mongo_solutions.read():
            item["_id"] = str(item["_id"])
            solutions.append(item)
        ret["solutions"] = solutions
        return ret

    def removeSolution(self):
        ret = {"code": 200}
        params = self._request_json.get("params")
        _id = params.get("_id")
        # 删除子任务
        for entry_id in self._mongo_solutions.read_one({"_id": ObjectId(_id)}).get("entryIdList"):
            entry = self._mongo_entry.read_one({"_id": ObjectId(entry_id)})
            # redis中删除相关id
            pids = list(entry.get("pid"))
            for pid in pids:
                self._redis.sRemove(self._redis_skuIds_key, str(pid))
            self._mongo_entry.delete({"_id": ObjectId(entry_id)})
        # 删除solutions set表中关于id的
        self._redis.sRemove(self._redis_Solutions_set_key, str(_id))
        # 删除solution
        self._mongo_solutions.delete({"_id": ObjectId(_id)})
        ret["message"] = f"删除Solution {_id} 成功！"
        return ret

    def pauseSolution(self):
        """
        暂停方案，redis_set内删除id，redis_set内删除skuids, 并标记已经暂停
        """
        ret = {"code": 200}
        params = self._request_json.get("params")
        _id = params.get("_id")
        solution = self._mongo_solutions.read_one({"_id": ObjectId(_id)})
        # 删除子任务中所有skuid
        for entry_id in solution.get("entryIdList"):
            entry = self._mongo_entry.read_one({"_id": ObjectId(entry_id)})
            # redis中stocks删除相关id
            pids = list(entry.get("pid"))
            for pid in pids:
                self._redis.sRemove(self._redis_skuIds_key, str(pid))
        # 删除solutions set表中关于id的
        self._redis.sRemove(self._redis_Solutions_set_key, str(_id))
        # 标记solution为暂停状态 1—>2
        solution["status"] = 2
        self._mongo_solutions.update({"_id":ObjectId(_id)}, {"$set": solution})
        ret["message"] = f"暂停Solution {_id} 成功！"
        return ret

    def recoverSolution(self):
        """
        重新恢复方案， redis_set中增加id，redis_set中重新加入skuids, 并标记已经
        """
        ret = {"code": 200}
        params = self._request_json.get("params")
        _id = params.get("_id")
        solution = self._mongo_solutions.read_one({"_id": ObjectId(_id)})
        # 删除子任务中所有skuid
        for entry_id in solution.get("entryIdList"):
            entry = self._mongo_entry.read_one({"_id": ObjectId(entry_id)})
            # redis中stocks增加相关id
            pids = list(entry.get("pid"))
            for pid in pids:
                self._redis.sAdd(self._redis_skuIds_key, str(pid))
        # 增加solutions set表中关于id的
        self._redis.sAdd(self._redis_Solutions_set_key, str(_id))
        # 标记solution为暂停状态 2—>1
        solution["status"] = 1
        self._mongo_solutions.update({"_id": ObjectId(_id)}, {"$set": solution})
        ret["message"] = f"启动Solution {_id} 成功！"
        return ret


    def post(self):
        method = request.get_json().get("method")
        if not method:
            abort(400)
        else:
            self._request_json = request.get_json()
        try:
            return self.optional[method]()
        except Exception as e:
            print(traceback.format_exc())
            return {"code": 500, "error": str(e)}


class ManageEntriesAPI(MethodView):
    """
    管理监控的任务列表
    """
    _mongo_entry = MongoSession(db="Gaze", col="JDEntries")
    _mongo_solutions = MongoSession(db="Gaze", col="JDSolutions")

    _redis = RedisSession()
    _redis_skuIds_key = "JDSkuIds:"
    _redis_Solutions_set_key = "JDSolutionsSet:"
    # 保存solution的metadata
    _redis_Solutions_metadata_key = "JDSolutionsMetadata:"
    _redis_Solutions_hash_key = "JDSolutionsHash:"

    def __init__(self):
        self.optional = dict()
        self.init_optional()
        self._request_json = None

    def init_optional(self):
        self.optional = {
            "addEntry": self.addEntry,
            "updateEntry": self.updateEntry,
            "removeEntry": self.removeEntry,
            "removeTasksAll": self.removeTasksAll,
            "listEntries": self.listEntries,
            "listEntriesByIdList": self.listEntriesByIdList,
            "activateEntry": self.activateEntry,
            "deactivateEntry": self.deactivateEntry
        }

    def addEntry(self):
        ret = {"code": 200}
        params = self._request_json.get("params")
        # 加入任务列表
        params.pop("_id")
        insertedId = str(self._mongo_entry.create(params))

        # entry所属解决方案增加一条entryId
        solution = self._mongo_solutions.read_one({"_id": ObjectId(params.get("father"))})
        solution["entryIdList"].append(insertedId)
        solution["size"] += 1
        self._mongo_solutions.update(where={"_id": ObjectId(params.get("father"))}, item={'$set': solution})

        # redis中加入pids
        pid = params.get("pid")
        for skuId in pid:
            self._redis.sAdd(self._redis_skuIds_key, str(skuId))
            # redis Solution:[sid] 中加入skuid:price
            self._redis.hSet(hash_key=self._redis_Solutions_hash_key + params.get("father"), key=str(skuId),
                             value=float(params.get("price")))

        ret["message"] = f"添加entry{insertedId}成功！"
        ret["entryId"] = insertedId
        return ret

    def updateEntry(self):
        ret = {"code": 200}
        params = self._request_json.get("params")
        _id = params.get("_id")
        where = {}
        params.pop("_id")
        where["_id"] = ObjectId(_id)
        # 将原来的entry内skuid删除掉 在solution中
        # redis stock中删除并重新插入
        skuIds = self._mongo_entry.read_one({"_id": ObjectId(_id)}).get("pid")
        for skuId in skuIds:
            self._redis.hRemove(hash_key=self._redis_Solutions_hash_key + params.get("father"), key=str(skuId))
            self._redis.sRemove(self._redis_skuIds_key, str(skuId))
        # 重新插入skuids 到hash表
        for skuId in params.get("pid"):
            self._redis.hSet(hash_key=self._redis_Solutions_hash_key + params.get("father"), key=str(skuId),
                             value=float(params.get("price")))
            self._redis.sAdd(self._redis_skuIds_key, str(skuId))
        self._mongo_entry.update(where, {'$set': params})

        ret["message"] = f"修改Entry {_id} 成功！"
        return ret

    # 激活entry
    def activateEntry(self):
        ret = {"code": 200}
        entry = self._request_json.get("params")
        _id = entry.get("_id")
        entry = self._mongo_entry.read_one({"_id": ObjectId(_id)})
        # 将原来的entry内skuid增加到 solution中
        for skuId in entry.get("pid"):
            self._redis.hSet(hash_key=self._redis_Solutions_hash_key + entry.get("father"), key=str(skuId),
                             value=float(self._mongo_entry.read_one({"_id": ObjectId(_id)}).get("price")))
            self._redis.sAdd(self._redis_skuIds_key, str(skuId))

        # 将mongo中entry状态设置为1
        entry["activate"] = 1
        self._mongo_entry.update({"_id": ObjectId(_id)}, {'$set': entry})
        ret["message"] = f"激活Entry {_id} 成功！"
        return ret

    # 暂停entry
    def deactivateEntry(self):
        ret = {"code": 200}
        entry = self._request_json.get("params")
        _id = entry.get("_id")
        entry = self._mongo_entry.read_one({"_id": ObjectId(_id)})
        # 将原来的entry内skuid删除 solution中
        for skuId in entry.get("pid"):
            self._redis.hRemove(hash_key=self._redis_Solutions_hash_key + entry.get("father"), key=str(skuId))
            self._redis.sRemove(self._redis_skuIds_key, str(skuId))

        # 将mongo中entry状态设置为1
        entry["activate"] = 2
        self._mongo_entry.update({"_id": ObjectId(_id)}, {'$set': entry})
        ret["message"] = f"暂停Entry {_id} 成功！"
        return ret

    # 激活全部entry
    def activateAllEntry(self):
        ret = {"code": 200}


        ret["message"] = f"激活全部Entry成功！"
        return ret

    def removeEntry(self):
        ret = {"code": 200}
        params = self._request_json.get("params")
        _id = params.get("_id")
        where = {}
        where["_id"] = ObjectId(_id)

        Entry = self._mongo_entry.read_one(where)
        if not Entry:
            ret["message"] = f"Entry {_id} 不存在！"
        # redis中删除相关id
        skuIds = list(Entry.get("pid"))
        for skuId in skuIds:
            self._redis.sRemove(self._redis_skuIds_key, str(skuId))
            self._redis.hRemove(hash_key=self._redis_Solutions_hash_key + params.get("father"), key=str(skuId))

        self._mongo_entry.delete(where)
        # 方案中删除entry
        solution = self._mongo_solutions.read_one({"_id": ObjectId(params.get("father"))})
        try:
            solution["entryIdList"].remove(_id)
            solution["size"] -= 1
            self._mongo_solutions.update(where={"_id": ObjectId(params.get("father"))}, item={'$set': solution})
        except Exception as e:
            print(e)
        ret["message"] = f"删除Entry {_id} 成功！"
        return ret

    def removeTasksAll(self):
        ret = {"code": 200}

        # 执行一次事务
        @self._mongo_entry.transaction
        def remove():
            for item in self._mongo_entry.read():
                item["_id"] = str(item["_id"])
                self._mongo_entry.delete({"_id": ObjectId(item["_id"])})

        remove()
        ret["message"] = f"删除所有Entry成功！"
        return ret

    def listEntries(self):
        ret = {"code": 200}
        Entries = []
        for item in self._mongo_entry.read():
            item["_id"] = str(item["_id"])
            Entries.append(item)
        ret["entries"] = Entries
        return ret

    def listEntriesByIdList(self):
        ret = {"code": 200}
        params = self._request_json.get("params")
        Entries = []
        if len(params) == 0:
            return ret
        for _id in params:
            item = self._mongo_entry.read_one(where={"_id": ObjectId(_id)})
            item["_id"] = str(item["_id"])
            Entries.append(item)
        ret["entries"] = Entries
        return ret

    def post(self):
        method = request.get_json().get("method")
        if not method:
            abort(400)
        else:
            self._request_json = request.get_json()
        try:
            return self.optional[method]()
        except Exception as e:
            print(traceback.format_exc())
            return {"code": 500, "error": str(e)}


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
                @self._mongoHistory.transaction
                def remove():
                    for item in self._mongoHistory.read():
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
    proxiesServer = ProxiesServer()

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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
            "Connection": "keep-alive",
            "User-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:86.0) Gecko/20100101 Firefox/86.0",
            "Host": "item.jd.com",
            "Upgrade-Insecure-Requests": "1"
        }
        cookies = {
            "__jda": "122270672.16159833264501252092042.1615983326.1615983326.1615983326.1",
            "__jdb": "122270672.4.16159833264501252092042|1.1615983326",
            "__jdc": "122270672",
            "__jdu": "16159833264501252092042",
            "__jdv": "122270672|direct|-|none|-|1615983326450",
            "_pst": "cycmay3",
            "_tp": "wJyuCv3+e0WMGi0eZ6MmGQ==",
            "3AB9D23F7A4B3C9B": "CHBVGIVSSK7DBBML5KYJA5OFZIFOUGMX3WQAM4MTF7GKLLCPD77TV4JD5GEUDZCFMQFNGWUATRSUMA3MWM35CQRWFQ",
            "areaId": "8",
            "ceshi3.com": "000",
            "ipLoc-djd": "8-560-50826-0",
            "pin": "cycmay3",
            "pinId": "8ZA4CfuvKyk",
            "shshshfp": "63d63c27f7544a3ab0e57e5ef578e53c",
            "shshshfpa": "c3a3fe3c-4270-7d8b-b4d7-734491a5b433-1615983384",
            "shshshfpb": "y/naGp8kz Td JU5n8qfyog==",
            "shshshsID": "473723aae248e6372b6feccf77fa7760_2_1615983398643",
            "thor": "F147DEA78F234763AA1C6928E9342CBA55C64A4C36BBE8C0157EF5BB4EA739E74ADC3594170CBD529CE357FC1C026004801842F9E20E18BE8817C369E280300457AC8FA6F117DFD6656AD796FFC3FA766EEC17CACD4D72DF37F8E01C59B5E194967B0FB90D7C965346F6C6530F081F143C2AF7D31DC69682B3E4567B6742B2BD0D92A394EC014BD4D4FABC9968E38E5C",
            "TrackID": "1CPMUblGMmaRUyvxiojktmwhIDCEs7B0hcn7toXPLesWVMSJRiIQMG08MvFPJFh_muH7cHmsTWyvdo7S-XMIAa6gmQ6FNrFr1oshZsuhP5i5HMcthbeoogYbTzJtJbOBz",
            "unick": "cycmay3",
            "wlfstk_smdl": "nld7xagcz5307wza73gynh96kutyji07"
        }
        # proxies = self.proxiesServer.get_random_proxy()
        proxies = {}
        # print(proxies)
        resp = requests.get(url=url, headers=headers, proxies=proxies, cookies=cookies)
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
                newer["tip"] = item.get("尺码", "None") + " " + item.get("颜色", "None")
                ret["pid_tip_map"].append(newer)
        else:
            # 没有colorsize 则为单品
            newer = {}
            newer["pid"] = skuid
            newer["tip"] = "单品"
            ret["pid_tip_map"].append(newer)

        return ret


api_v1.add_url_rule('/JDtask/manageStocks', view_func=ManageStocksAPI.as_view('api_JDtaskManageStocks'),
                    methods=["POST"])
api_v1.add_url_rule('/JDtask/manageEntries', view_func=ManageEntriesAPI.as_view('api_JDtaskManageEntries'),
                    methods=["POST"])
api_v1.add_url_rule('/JDtask/manageSolutions', view_func=ManageSolutionsAPI.as_view('api_JDtaskManageSolutions'),
                    methods=["POST"])
api_v1.add_url_rule('/JDtask/manageHistoryTasks',
                    view_func=ManageHistroyTasksAPI.as_view('api_JDtaskManageHistoryTasks'), methods=["POST"])
api_v1.add_url_rule('/JDtask/getParsePromoteUrl',
                    view_func=GetParsePromoteUrlAPI.as_view('api_JDtaskGetParsePromoteUrl'), methods=["POST"])
