from flask import render_template, request, Blueprint

from app.extensions import api_config
from app.extensions import db
from app.forms import BuyItemForm
from app.models import Buyitem
from app.models import du_product

buyitems_bp = Blueprint('buyitems', __name__)


@buyitems_bp.route('/buyitems')
def buyitems():
    all_count = Buyitem.query.count()
    items = Buyitem.query.all()
    sizelist = api_config.get("size")
    buy_type = api_config.get("buy_type")
    sold_type = api_config.get("sold_type")
    return render_template('buyitems.html', items=items,
                           all_count=all_count, size_list=sizelist,
                           buy_type=buy_type, sold_type=sold_type,
                           )
# @buyitem_bp.route('/edit_buyitems', methods=["GET", "POST"])
# def edit_buyitems():
#     buyitemsForm = BuyItemForm()

@buyitems_bp.route('/add_buyitems', methods=['GET', 'POST'])
def add_buyitems():
    sizelist = api_config.get("size")
    buy_type = api_config.get("buy_type")
    sold_type = api_config.get("sold_type")
    buyitemsForm = BuyItemForm()
    if request.method == "POST":
        data = {
            "name": request.form.get('name'),
            "productId": request.form.get('productId'),
            "size": request.form.get('size'),
            "buyTypeId": str(request.form.get('buyTypeId')),
            "buyCost": float(request.form.get('buyCost')),
            "soldTypeId": str(request.form.get('soldTypeId')),
            "buyTime": request.form.get('buyTime'),
            "soldPriceExpect": float(request.form.get('soldPriceExpect')),
            # 置出价为期望出价
            "soldPrice": float(request.form.get("soldPriceExpect")),
            # 置购买后状态为已购买未收货装填
            "goodStatus": str("1"),
        }

        # 查询产品详细信息
        product = du_product.objects(productId=data.get("productId"))[:1][0]
        if product:
            data["articleNumber"] = product.articleNumber
            data["imageUrl"] = product.logoUrl

        # 计算预计利润
        data["profitExpect"] = profit_expect(data)
        # 计算预计利润率
        data["interestRateExpect"] = round(data.get("profitExpect") / data.get("buyCost"), 4)
        data["interestRate"] = data["interestRateExpect"]
        db.session.add(Buyitem(
            name=data.get("name"),
            articleNumber=data.get("articleNumber"),
            size=data.get("size"),
            buyCost=data.get("buyCost"),
            buyCharge=data.get("buyCharge"),
            soldTypeId=data.get("soldTypeId"),
            soldCharge=data.get("soldCharge"),
            imageUrl=data.get("imageUrl"),
            buyTypeId=data.get("buyTypeId"),
            soldPrice=data.get("soldPrice"),
            soldPriceExpect=data.get("soldPriceExpect"),
            profitExpect=data.get("profitExpect"),
            profit=data.get("profit"),
            interestRate=data.get("interestRate"),
            interestRateExpect=data.get("interestRateExpect"),
            goodStatus=data.get("goodStatus"),
            buyTime=data.get("buyTime"),
            soldTime=data.get("soldTime"),
        ))
        return {
            "code": 200,
            "message": "添加成功！"
        }

    return render_template('add_buyitems.html', size_list=sizelist,
                           buy_type=buy_type, sold_type=sold_type,
                           buyitemsForm=buyitemsForm
                           )


# 计算预计利润
def profit_expect(data: dict):
    """
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
    # 得物 寄存商品费率
    if data.get("soldTypeId") == "1" and data.get("soldPrice"):
        data["soldCharge"] = round(data.get("soldPrice") * api_config.get("sold_rate").get("0").get("commodity_rate"),
                                   2)
    # 得物 现货商品费率
    if data.get("soldType") == "2" and data.get("soldPrice"):
        data["soldCharge"] = round(data.get("soldPrice") * api_config.get("sold_rate").get("1").get("commodity_rate"),
                                   2)

    # 杂费
    if data.get("soldTypeId") == "1" or data.get("soldTypeId") == "2":
        data["soldCharge"] += round(
            data.get("soldPrice") * api_config.get("sold_rate").get(data.get("soldTypeId")).get("transfer_service_fee"),
            2)
        data["soldCharge"] += api_config.get("sold_rate").get(data.get("soldTypeId")).get("inspection_fee")
        data["soldCharge"] += api_config.get("sold_rate").get(data.get("soldTypeId")).get("identification_fee")
        data["soldCharge"] += api_config.get("sold_rate").get(data.get("soldTypeId")).get("packing_service_fee")

    if data.get("buyCost") and data.get("soldPrice"):
        data["profit"] = data.get("soldPrice") - data.get("buyCost")
    if data.get("sendCost"):
        data["profit"] = data.get("profit") - data.get("sendCost")
    if (data.get("soldTypeId") == "1" or data.get("buyTypeId") == "2") and data.get("soldPrice"):
        data["profit"] -= data.get("soldCharge")

    return data.get("profit")
