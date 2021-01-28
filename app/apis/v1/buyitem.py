from flask import request, jsonify, current_app
from flask.views import MethodView
from sqlalchemy.sql import func

from app.apis.v1 import api_v1
from app.apis.v1.schemas import buyitems_schema, duProducts_schema, buyitemsOverview_schema
from app.extensions import api_config
from app.extensions import db
from app.models import Buyitem, du_product


class GetBuyitemsAPI(MethodView):
    """
    获取已购项目信息
    """

    def get(self):
        currentPage = int(request.args.get('currentPage'))
        showCount = int(request.args.get("showCount"))

        goodStatus = request.args.get("goodStatus", None)
        if goodStatus:
            buyitems = Buyitem.query.filter(Buyitem.goodStatus == goodStatus).offset(
                (currentPage - 1) * showCount).limit(showCount)
            totalCount = Buyitem.query.filter(Buyitem.goodStatus == goodStatus).count()
        else:
            buyitems = Buyitem.query.offset(
                (currentPage - 1) * showCount).limit(showCount)
            totalCount = Buyitem.query.count()

        return jsonify(buyitems_schema(totalCount, buyitems))


class DuProductsAPI(MethodView):
    """
        通过键入关键字货号模糊查询
    """

    def get(self):
        keyword = request.args.get('keyword', '666', type=str)
        products = du_product.objects(articleNumber__contains=keyword)[:
                                                                       current_app.config["DUPRODUCT_ITEM_PRE_PAGE"]]
        return jsonify(duProducts_schema(products))


class GetBuyitemsOverview(MethodView):
    """
    获取已购买商品的总览信息
    """

    def get(self):
        data = {}
        # 待收货
        data["to_be_received"] = Buyitem.query.filter(Buyitem.goodStatus == 1).count()
        # 待出售
        data["to_be_sold"] = Buyitem.query.filter(Buyitem.goodStatus == 2).count()
        # 正在出售
        data["on_sale"] = Buyitem.query.filter(Buyitem.goodStatus == 3).count()
        # 已出售
        data["has_been_sold"] = Buyitem.query.filter(Buyitem.goodStatus == 4).count()

        # 实际盈利 选取已经售出的商品
        data["profit"] = round(
            float(Buyitem.query.with_entities(func.sum(Buyitem.profit)).filter(Buyitem.goodStatus == 4).scalar()), 2)

        # 实际成本 选取已经售出的商品
        data["total_buy_cost"] = round(
            float(Buyitem.query.with_entities(func.sum(Buyitem.buyCost)).filter(Buyitem.goodStatus == 4).scalar()), 2)

        data["total_cost"] = round(
            float(Buyitem.query.with_entities(func.sum(Buyitem.buyCost)).filter(Buyitem.goodStatus == 4).scalar()), 2)
        # 总销售额 统计所有已经出售的商品
        data["sold_total"] = round(
            float(Buyitem.query.with_entities(func.sum(Buyitem.soldPrice)).filter(Buyitem.goodStatus == 4).scalar()), 2)

        # 利率比
        if (data['profit'] and data['total_cost']):
            data['ceil'] = round(data['profit'] / data['total_cost'], 4) * 100
        else:
            data['ceil'] = 0

        # 预计盈利
        data["profit_expect"] = round(float(Buyitem.query.with_entities(func.sum(Buyitem.profitExpect)).scalar()), 2)
        # 预计成本
        data['cost_future'] = round(float(Buyitem.query.with_entities(func.sum(Buyitem.buyCost)).scalar()), 2)
        # 预计利率比
        data['ceil_future'] = 0
        if (data['cost_future']):
            data['ceil_future'] = round(data['profit_expect'] / data['cost_future'], 4) * 100

        return jsonify(buyitemsOverview_schema(data))


class AlterBuyitemAPI(MethodView):
    """
    修改或增加buyitem值
    """

    def post(self):
        buyitem = request.get_json().get("buyitem")
        if buyitem.get("submitState") == "Add":
            buyitem["buyCost"] = float(buyitem.get("buyCost"))
            buyitem["soldPriceExpect"] = float(buyitem.get("soldPriceExpect"))
            # 置出价为期望出价
            buyitem["soldPrice"] = float(buyitem.get("soldPriceExpect"))
            # 置购买后状态为已购买未收货
            buyitem["goodStatus"] = str("1")

            productId = buyitem.get("productId")
            duProduct = du_product.objects(productId=productId).first()
            # 计算预计利润
            buyitem["profitExpect"] = profit_expect(buyitem)
            # 计算预计利润率
            buyitem["interestRateExpect"] = round(buyitem.get("profitExpect") / buyitem.get("buyCost"), 4)
            buyitem["interestRate"] = buyitem["interestRateExpect"]

            db.session.add(Buyitem(
                name=duProduct.title,
                articleNumber=duProduct.articleNumber,
                size=buyitem.get("size"),
                buyCost=buyitem.get("buyCost"),
                buyCharge=buyitem.get("buyCharge"),
                soldTypeId=buyitem.get("soldTypeId"),
                soldCharge=buyitem.get("soldCharge"),
                imageUrl=duProduct.logoUrl,
                buyTypeId=buyitem.get("buyTypeId"),
                soldPriceExpect=buyitem.get("soldPriceExpect"),
                profitExpect=buyitem.get("profitExpect"),
                interestRateExpect=buyitem.get("interestRateExpect"),
                goodStatus=buyitem.get("goodStatus"),
                buyTime=str(buyitem.get("buyTime")),
            ))
            db.session.commit()
            return {
                "code": 200,
                "message": f"添加{duProduct.title}成功！"
            }
        elif buyitem.get("submitState") == "Upd":
            buyitem_id = buyitem.get("id")

            buyitem["buyCost"] = float(buyitem.get("buyCost"))
            buyitem["soldPriceExpect"] = float(buyitem.get("soldPriceExpect"))

            # 没有出价置出价为期望出价
            if not buyitem.get("soldPrice"):
                buyitem["soldPrice"] = float(buyitem.get("soldPriceExpect"))
                # 计算预计利润
                buyitem["profitExpect"] = round(profit_expect(buyitem), 2)
                # 计算预计利润率
                buyitem["interestRateExpect"] = round(buyitem.get("profitExpect") / buyitem.get("buyCost"), 4)
                buyitem["interestRate"] = buyitem["interestRateExpect"]

                Buyitem.query.filter(Buyitem.id == buyitem_id).update(
                    {

                        "size": buyitem.get("size"),
                        "buyCost": buyitem.get("buyCost"),
                        "buyCharge": buyitem.get("buyCharge"),
                        "soldTypeId": buyitem.get("soldTypeId"),
                        "buyTypeId": buyitem.get("buyTypeId"),
                        "soldPriceExpect": buyitem.get("soldPriceExpect"),
                        "profitExpect": buyitem.get("profitExpect"),
                        "interestRateExpect": buyitem.get("interestRateExpect"),
                        "buyTime": buyitem.get("buyTime")
                    }
                )
            else:
                # 出售商品计算利润
                buyitem["profit"] = round(profit_expect(buyitem), 2)
                buyitem["interestRate"] = round(buyitem.get("profit") / buyitem.get("buyCost"), 4)
                Buyitem.query.filter(Buyitem.id == buyitem_id).update(
                    {
                        "soldTypeId": buyitem.get("soldTypeId"),
                        "soldCharge": buyitem.get("soldCharge"),
                        "soldTime": buyitem.get("soldTime"),
                        "soldPrice": buyitem.get("soldPrice"),
                        "profit": round(buyitem.get("profit"), 2),
                        "interestRate": buyitem.get("interestRate"),
                        "goodStatus": buyitem.get("goodStatus")
                    }
                )
            db.session.commit()
            return {
                "code": 200,
                "message": f"修改{buyitem_id}成功！"
            }
        elif buyitem.get("submitState") == "Del":
            buyitem_id = buyitem.get("id")
            Buyitem.query.filter(Buyitem.id == buyitem_id).delete()
            db.session.commit()
            return {
                "code": 200,
                "message": f"删除{buyitem.get('title')}成功！"
            }


api_v1.add_url_rule('/getBuyitems', view_func=GetBuyitemsAPI.as_view('api_getbuyitems'), methods=["GET", "POST"])
api_v1.add_url_rule('/duproducts', view_func=DuProductsAPI.as_view('api_duproducts'), methods=["GET"])
api_v1.add_url_rule('/alterBuyitem', view_func=AlterBuyitemAPI.as_view('api_alterbuyitem'), methods=["POST"])
api_v1.add_url_rule('/getBuyitemsOverview', view_func=GetBuyitemsOverview.as_view('api_getbuyitemoverview'),
                    methods=["GET", "POST"])


# 计算预计利润
def profit_expect(data: dict):
    """
     data需提供：soldTypeId soldPrice buyCost
         // 出售平台 毒
            // 寄存
            // 费用明细：
            // 商品费率 5%，下限35，上限249 限时费率1.5%
            // 查验费 鞋类8元，非鞋类10元
            // 鉴别费 鞋类15元，非鞋类18元
            // 包装服务费 鞋类、非鞋类均为10元
            // 转账服务费 1%
            // 仓储费 免30天（自获得出价权限开始）
    """
    data["soldCharge"] = 0.0
    data["profit"] = 0.0
    sold_price = float(data.get("soldPrice")) if data.get("soldPrice") else None
    # 得物 寄存商品费率
    if data.get("soldTypeId") == "1" and sold_price:
        data["soldCharge"] = round(float(sold_price) * api_config.get("sold_rate").get("1").get("commodity_rate"),
                                   2)
    # 得物 现货商品费率
    if data.get("soldTypeId") == "2" and sold_price:
        data["soldCharge"] = round(sold_price * api_config.get("sold_rate").get("2").get("commodity_rate"),
                                   2)

    # 杂费
    if data.get("soldTypeId") == "1" or data.get("soldTypeId") == "2":
        data["soldCharge"] += round(
            sold_price * api_config.get("sold_rate").get(data.get("soldTypeId")).get("transfer_service_fee"),
            2)
        data["soldCharge"] += api_config.get("sold_rate").get(data.get("soldTypeId")).get("inspection_fee")
        data["soldCharge"] += api_config.get("sold_rate").get(data.get("soldTypeId")).get("identification_fee")
        data["soldCharge"] += api_config.get("sold_rate").get(data.get("soldTypeId")).get("packing_service_fee")

    if data.get("buyCost") and sold_price:
        data["profit"] = sold_price - data.get("buyCost")
    if data.get("sendCost"):
        data["profit"] = data.get("profit") - data.get("sendCost")
    if (data.get("soldTypeId") == "1" or data.get("buyTypeId") == "2") and sold_price:
        data["profit"] -= data.get("soldCharge")

    return data.get("profit")
