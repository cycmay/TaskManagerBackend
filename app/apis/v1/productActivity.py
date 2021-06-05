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
from app.models import ActivityForecast,Activities

from app.extensions import db

import requests


class GetForecastActivityProductsAPI(MethodView):
    """
    获取活动产品数据
    """
    exists = 1

    def get(self):
        currentPage = int(request.args.get('currentPage'))
        showCount = int(request.args.get("showCount"))
        activityId = str(request.args.get("activityId"))
        minInterestRate = 0.0
        minDuSoldNum = 0

        if request.args.get("minInterestRate"):
            minInterestRate = float(request.args.get("minInterestRate"))
        if request.args.get("minDuSoldNum"):
            minDuSoldNum = int(request.args.get("minDuSoldNum"))

        products = ActivityForecast.query.filter(ActivityForecast.activityId == activityId,
                                         ActivityForecast.interestRate > minInterestRate,
                                         ActivityForecast.duSoldNum > minDuSoldNum,
                                         ActivityForecast.stock == self.exists, # 有货
                                         ). \
            order_by(ActivityForecast.stock.desc(), ActivityForecast.interestRate.desc()).offset((currentPage - 1) * showCount). \
            limit(showCount)
        totalCount = ActivityForecast.query.filter(ActivityForecast.activityId == activityId,
                                           ActivityForecast.interestRate > minInterestRate,
                                           ActivityForecast.duSoldNum > minDuSoldNum,
                                           ActivityForecast.stock == self.exists, # 有货
                                        ).count()

        return jsonify(products_schema(totalCount, products))


class GetForecastActivitiesAPI(MethodView):
    """
    获取活动列表
    """

    def get(self):
        activities = Activities.query.all()
        totalCount = Activities.query.count()

        return jsonify(activities_schema(totalCount, activities))



api_v1.add_url_rule('/JDForecast/getActivityForecastProducts',
                    view_func=GetForecastActivityProductsAPI.as_view('api_getactivityforecastproducts'), methods=["GET", "POST"])
api_v1.add_url_rule('/JDForecast/getForecastActivities',
                    view_func=GetForecastActivitiesAPI.as_view('api_getforecastactivities'), methods=["GET", "POST"])


def product_schema(item):
    return {
        "id": item.id,
        "activityId": item.activityId,
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
        "stock": int(item.stock) if item.stock else 0,
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

def activity_schema(item):
    return {
        "id": item.id,
        "activityId": item.activityId,
        "vendorId": item.vendorId,
        "activityname": item.activityname,
        "activitydiscount": round(float(item.activitydiscount), 4)
    }


def activities_schema(totalCount, items):
    return {
        "code": 200,
        "data": {
            "totalCount": totalCount,
            "activities": [activity_schema(item) for item in items]
        }
    }

