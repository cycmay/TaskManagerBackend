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

