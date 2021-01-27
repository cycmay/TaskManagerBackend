

from itertools import product

from app.extensions import api_config


def duProduct_schema(item):
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
    buy_type = api_config.get("buy_type")
    sold_type = api_config.get("sold_type")
    good_status = api_config.get("good_status")
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