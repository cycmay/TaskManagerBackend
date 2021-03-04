import time

from sqlalchemy.sql.schema import ForeignKey
from app.extensions import db, mongodb_du
import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)

    def __repr__(self):
        return '<User %r>'%self.nickname


class Buyitem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(255))
    articleNumber = db.Column(db.String(255))
    size = db.Column(db.String(32))
    buyCost = db.Column(db.DECIMAL(10,2))
    buyCharge = db.Column(db.DECIMAL(10,2))
    soldTypeId = db.Column(db.Integer)
    soldCharge = db.Column(db.DECIMAL(10,2))
    imageUrl = db.Column(db.String(255))
    buyTypeId = db.Column(db.Integer)
    soldPrice = db.Column(db.DECIMAL(10,2))
    soldPriceExpect = db.Column(db.DECIMAL(10,2))
    profitExpect = db.Column(db.DECIMAL(10,2))
    profit = db.Column(db.DECIMAL(10,2))
    interestRate = db.Column(db.DECIMAL(10,2))
    interestRateExpect = db.Column(db.DECIMAL(10,2))
    goodStatus = db.Column(db.Integer)
    buyTime = db.Column(db.String(32))
    soldTime = db.Column(db.String(32))
    create_at = db.Column(db.DATETIME, default=datetime.datetime.now)

# 进行计算得出利润排序
class Forecast(db.Model):
    # 绑定的查询数据库
    __tablename__ = 'forecast'
    __table_args__ = {'schema': 'JDTracker'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # jd的商品id
    productId = db.Column(db.String(32))
    vendorId = db.Column(db.String(32))
    articleNumber = db.Column(db.String(32))
    title = db.Column(db.String(255))
    # jd的商品标价
    price = db.Column(db.DECIMAL(10, 2))
    # 打完折的价格
    finalPrice = db.Column(db.DECIMAL(10, 2))
    # 尺码
    size = db.Column(db.String(32))
    # 得物现货价格
    duPrice = db.Column(db.DECIMAL(10, 2))
    # 得物销量
    duSoldNum = db.Column(db.Integer)
    # 价差
    gap = db.Column(db.DECIMAL(10, 2))
    # 到手利润
    interest = db.Column(db.DECIMAL(10, 2))
    # 到手利润率
    interestRate = db.Column(db.DECIMAL(10, 4))
    # 商品图片
    imageUrl = db.Column(db.String(255))
    # 商品地址
    itemUrl = db.Column(db.String(255))

    # 状态 0 有货 1 无货
    stock = db.Column(db.Integer)

    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


# 唯品会商品
class VIPForecast(db.Model):
    # 绑定的查询数据库
    __tablename__ = 'vipforecast'
    __table_args__ = {'schema': 'JDTracker'}
    # __bind_key__ = 'JDTracker'
    # __tablename__ = 'vipforecast'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # jd的商品id
    productId = db.Column(db.String(32))
    vendorId = db.Column(db.String(32))
    articleNumber = db.Column(db.String(32))
    title = db.Column(db.String(255))
    # jd的商品标价
    price = db.Column(db.DECIMAL(10,2))
    # 打完折的价格
    finalPrice = db.Column(db.DECIMAL(10,2))
    # 尺码
    size = db.Column(db.String(32))
    # 得物现货价格
    duPrice = db.Column(db.DECIMAL(10,2))
    # 得物销量
    duSoldNum = db.Column(db.Integer)
    # 价差
    gap = db.Column(db.DECIMAL(10,2))
    # 到手利润
    interest = db.Column(db.DECIMAL(10,2))
    # 到手利润率
    interestRate = db.Column(db.DECIMAL(10,4))
    # 商品图片
    imageUrl = db.Column(db.String(255))
    # 商品地址
    itemUrl = db.Column(db.String(255))

    # 状态 0 有货 1 无货
    stock = db.Column(db.Integer)


class Shops(db.Model):
    # 绑定的查询数据库
    __bind_key__ = 'JDTracker'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    shopId = db.Column(db.String(32))
    vendorId = db.Column(db.String(32))
    shopname = db.Column(db.String(32))
    shopdiscount = db.Column(db.DECIMAL(10,4))




class du_product(mongodb_du.Document):
    """
    du mongodb的数据类型
    """
    productId = mongodb_du.IntField()
    articleNumber = mongodb_du.StringField()
    title = mongodb_du.StringField()
    sellDate = mongodb_du.StringField()
    logoUrl = mongodb_du.StringField()
    authPrice = mongodb_du.IntField()
    soldNum = mongodb_du.IntField()
    priceList = mongodb_du.ListField()
    updateTime = mongodb_du.DateTimeField()

