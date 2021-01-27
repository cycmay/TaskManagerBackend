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
from app.domain.MongoSession import MongoSession
from app.domain.RedisSession import RedisSession
from app.extensions import api_config
from app.models import Forecast, Shops, VIPForecast

from app.extensions import db

import requests


class GetForecastProductsAPI(MethodView):
    """
    获取预测产品数据
    """

    def get(self):
        currentPage = int(request.args.get('currentPage'))
        showCount = int(request.args.get("showCount"))
        vendorId = str(request.args.get("vendorId"))
        minInterestRate = 0.0
        minDuSoldNum = 0

        if request.args.get("minInterestRate"):
            minInterestRate = float(request.args.get("minInterestRate"))
        if request.args.get("minDuSoldNum"):
            minDuSoldNum = int(request.args.get("minDuSoldNum"))

        products = Forecast.query.filter(Forecast.vendorId == vendorId,
                                         Forecast.interestRate > minInterestRate,
                                         Forecast.duSoldNum > minDuSoldNum,
                                         ). \
            order_by(Forecast.interestRate.desc()).offset((currentPage - 1) * showCount). \
            limit(showCount)
        totalCount = Forecast.query.filter(Forecast.vendorId == vendorId,
                                           Forecast.interestRate > minInterestRate,
                                           Forecast.duSoldNum > minDuSoldNum, ).count()

        return jsonify(products_schema(totalCount, products))

class GetVIPForecastProductsAPI(MethodView):
    """
    获取唯品会预测产品数据
    """

    def get(self):
        currentPage = int(request.args.get('currentPage'))
        showCount = int(request.args.get("showCount"))
        minInterestRate = 0.0
        minDuSoldNum = 0

        if request.args.get("minInterestRate"):
            minInterestRate = float(request.args.get("minInterestRate"))
        if request.args.get("minDuSoldNum"):
            minDuSoldNum = int(request.args.get("minDuSoldNum"))

        products = VIPForecast.query.filter(
                                        VIPForecast.interestRate > minInterestRate,
                                         VIPForecast.duSoldNum > minDuSoldNum,
                                         ). \
            order_by(VIPForecast.interestRate.desc()).offset((currentPage - 1) * showCount). \
            limit(showCount)
        totalCount = VIPForecast.query.filter(VIPForecast.interestRate > minInterestRate,
                                           VIPForecast.duSoldNum > minDuSoldNum, ).count()

        return jsonify(products_schema(totalCount, products))


class GetForecastShopsAPI(MethodView):
    """
    获取店铺列表
    """

    def get(self):
        shops = Shops.query.all()
        totalCount = Shops.query.count()

        return jsonify(shops_schema(totalCount, shops))


api_v1.add_url_rule('/JDForecast/getForecastProducts',
                    view_func=GetForecastProductsAPI.as_view('api_getforecastproducts'), methods=["GET", "POST"])
api_v1.add_url_rule('/JDForecast/getVIPForecastProducts',
                    view_func=GetVIPForecastProductsAPI.as_view('api_getvipforecastproducts'), methods=["GET", "POST"])
api_v1.add_url_rule('/JDForecast/getForecastShops',
                    view_func=GetForecastShopsAPI.as_view('api_getforecastshops'), methods=["GET", "POST"])


def product_schema(item):
    return {
        "id": item.id,
        "productId": item.productId,
        "vendorId": item.vendorId,
        "articleNumber": item.articleNumber,
        "title": item.title,
        "price": round(float(item.price if item.price else 0.0), 2),
        "finalPrice": round(float(item.finalPrice if item.finalPrice else 0.0), 2),
        "size": item.size,
        "duPrice": round(float(item.duPrice if item.duPrice else 0.0), 2),
        "duSoldNum": int(item.duSoldNum),
        "gap": round(float(item.gap if item.gap else 0.0), 2),
        "interest": round(float(item.interest if item.interest else 0.0), 2),
        "interestRate": round(float(item.interestRate if item.interestRate else 0.0), 4),
        "imageUrl": item.imageUrl,
        "itemUrl": item.itemUrl
    }


def products_schema(totalCount, items):
    return {
        "code": 200,
        "data": {
            "totalCount": totalCount,
            "products": [product_schema(item) for item in items]
        }
    }


def shop_schema(item):
    return {
        "id": item.id,
        "shopId": item.shopId,
        "vendorId": item.vendorId,
        "shopname": item.shopname,
        "shopdiscount": round(float(item.shopdiscount), 4)
    }


def shops_schema(totalCount, items):
    return {
        "code": 200,
        "data": {
            "totalCount": totalCount,
            "shops": [shop_schema(item) for item in items]
        }
    }
