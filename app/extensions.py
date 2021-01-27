from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from flask_mongoengine import MongoEngine

from flask_pymongo import PyMongo

db = SQLAlchemy()
csrf = CSRFProtect()

mongodb_du = MongoEngine()

# 字典列表
api_config = {
    'size': {
        '0': '35.5',
        '1': '36',
        '2': '36.5',
        '3': '37',
        '4': '37.5',
        '5': '38',
        '6': '38.5',
        '7': '39',
        '8': '39.5',
        '9': '40',
        '10': '40.5',
        '11': '41',
        '12': '41.5',
        '13': '42',
        '14': '42.5',
        '15': '43',
        '16': '43.5',
        '17': '44',
        '18': '44.5',
        '19': '45',
        '20': '45.5',
        '21': 'XS',
        '22': 'S',
        '23': 'M',
        '24': 'L',
        '25': 'XL',
        '26': 'XXL',
        '27': 'XXXL'
    },
    'buy_type': {
        "0": "无",
        "1": "京东",
        "2": "淘宝",
        "3": "其他"
    },
    'sold_type': {
        "0": "无",
        "1": "毒-寄存",
        "2": "毒-现货",
        "3": "咸鱼",
    },
    'good_status': {
        "0": "无状态",
        "1": "已购买未收货",
        "2": "已收货未出售",
        "3": "正在出售",
        "4": "已售出"
    },
    # // 售卖费率
    'sold_rate': {
        '0': {},
        # 得物寄存
        "1": {
            # 商品费率
            'commodity_rate': 0.015,
            # 查验费
            'inspection_fee': 8,
            # 鉴别费
            'identification_fee': 15,
            # 包装服务费
            'packing_service_fee': 10,
            # 转账服务费
            'transfer_service_fee': 0.01,
        },
        # 得物现货
        "2": {
            # 商品费率
            'commodity_rate': 0.05,
            # 商品费率下限
            'commodity_fee_limit': 15,
            # 查验费
            'inspect'
            'ion_fee': 8,
            # 鉴别费
            'identification_fee': 15,
            # 包装服务费
            'packing_service_fee': 10,
            # 转账服务费
            'transfer_service_fee': 0.01,
        }
    }


}