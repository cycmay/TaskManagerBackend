from flask import jsonify
from flask.views import MethodView

from app.apis.v1 import api_v1
from app.apis.v1.schemas import sizeList_schema, buyTypeId_schema, soldTypeId_schema, goodStatusMap_schema
from app.extensions import api_config


class IndexAPI(MethodView):

    def get(self):
        return jsonify({
            "api_version": "1.0",
            "api_base_url": "http://example.com/api/v1",
        })


class GetBuyitemsSizeAPI(MethodView):
    """
    获取size列表
    """
    def get(self):
        sizelist = api_config.get("size")
        return jsonify(sizeList_schema(sizelist))

class GetBuyTypeIdAPI(MethodView):
    """
    获取购买平台列表
    """
    def get(self):
        buyTypeIdList = api_config.get("buy_type")
        return jsonify(buyTypeId_schema(buyTypeIdList))

class GetSoldTypeIdAPI(MethodView):
    """
    获取出售平台列表
    """
    def get(self):
        soldTypeIdList = api_config.get("sold_type")
        return jsonify(soldTypeId_schema(soldTypeIdList))

class getBuyitemsGoodStatusMapAPI(MethodView):
    """
    获取buyitems goodstatus 映射表
    """
    def get(self):
        goodStatusMap = api_config.get("good_status")
        return jsonify(goodStatusMap_schema(goodStatusMap))


api_v1.add_url_rule('/', view_func=IndexAPI.as_view('api_index'), methods=['GET'])
api_v1.add_url_rule('/getBuyitemsSize', view_func=GetBuyitemsSizeAPI.as_view('api_getbuyitemssize'), methods=["GET"])
api_v1.add_url_rule('/getBuyitemsBuyTypeID', view_func=GetBuyTypeIdAPI.as_view('api_getbuytypeid'), methods=["GET"])
api_v1.add_url_rule('/getBuyitemsSoldTypeID', view_func=GetSoldTypeIdAPI.as_view('api_getsoldtypeid'), methods=["GET"])
api_v1.add_url_rule('/getBuyitemsGoodStatusMap', view_func=getBuyitemsGoodStatusMapAPI.as_view('api_getgoodstatusmap'), methods=["GET"])
