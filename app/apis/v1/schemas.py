

from itertools import product

from app.extensions import api_config


def duProduct_schema(item):
    if not item:
        return {}
    return {
        "productId": item.productId,
        "articleNumber": item.articleNumber,
        "title": item.title,
        "sellDate": item.sellDate,
        "logoUrl": item.logoUrl,
        "authPrice": item.authPrice,
        "soldNum": item.soldNum,
        "priceList": item.priceList,
        "updateTime": item.updateTime,
    }


def duProducts_schema(items):
    return {
        "code": 200,
        "data": {
            "products": [duProduct_schema(item) for item in items]
        }
    }

def buyitem_schema(item):
    return {
        "id": item.id,
        "name": item.name,
        "articleNumber": item.articleNumber,
        "size": item.size,
        "buyCost": round(float(item.buyCost if item.buyCost else 0.0), 2),
        "buyCharge": round(float(item.buyCharge if item.buyCharge else 0.0), 2),
        "soldTypeId": str(item.soldTypeId),
        "soldCharge": round(float(item.soldCharge if item.soldCharge else 0.0), 2),
        "imageUrl": item.imageUrl,
        "buyTypeId": str(item.buyTypeId),
        "soldPrice": round(float(item.soldPrice if item.soldPrice else 0.0), 2),
        "soldPriceExpect": round(float(item.soldPriceExpect if item.soldPriceExpect else 0.0), 2),
        "profitExpect": round(float(item.profitExpect if item.profitExpect else 0.0), 2),
        "profit": round(float(item.profit if item.profit else 0.0), 2),
        "interestRate": round(float(item.interestRate if item.interestRate else 0.0), 2),
        "interestRateExpect": round(float(item.interestRateExpect if item.interestRateExpect else 0.0), 2),
        "goodStatus": str(item.goodStatus),
        "buyTime": item.buyTime,
        "soldTime": item.soldTime,
    }

def buyitemsOverview_schema(item):
    return {
        "code": 200,
        "data": {
            "to_be_received": item.get("to_be_received"),
            "to_be_sold": item.get("to_be_sold"),
            "on_sale": item.get("on_sale"),
            "has_been_sold": item.get("has_been_sold"),
            "profit": item.get("profit"),
            "total_buy_cost": item.get("total_buy_cost"),
            "total_cost": item.get("total_cost"),
            "sold_total": item.get("sold_total"),
            "ceil": item.get("ceil"),
            "profit_expect": item.get("profit_expect"),
            "cost_future": item.get("cost_future"),
            "ceil_future": item.get("ceil_future")
        }
    }

def buyitems_schema(totalCount, items):
    return {
        "code": 200,
        "data": {
            "totalCount": totalCount,
            "buyitems": [buyitem_schema(item) for item in items]
        }
    }

def sizeList_schema(sizeList:dict):
    return {
        "code": 200,
        "data": {
            "sizeList": sizeList
        }
    }

def buyTypeId_schema(buyTypeIdList:dict):
    return {
        "code": 200,
        "data": {
            "buyTypeIdList": buyTypeIdList
        }
    }

def soldTypeId_schema(soldTypeIdList:dict):
    return {
        "code": 200,
        "data": {
            "soldTypeIdList": soldTypeIdList
        }
    }

def goodStatusMap_schema(goodStatusMap:dict):
    return {
        "code": 200,
        "data": {
            "goodStatusMap": goodStatusMap
        }
    }