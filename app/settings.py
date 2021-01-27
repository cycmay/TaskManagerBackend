from logging import DEBUG
import os

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class BaseConfig:
    # TODO:CSRF验证
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'respect'

    DIALECT = 'mysql'
    DRIVER = 'pymysql'
    USERNAME = 'root'
    PASSWORD = 'cyc19971215.'
    HOST = '127.0.0.1'
    PORT = '3306'
    DATABASE = 'TaskManager'

    # du商品获取分页
    DUPRODUCT_ITEM_PRE_PAGE = 8

    # 默认数据库
    SQLALCHEMY_DATABASE_URI = '{}+{}://{}:{}@{}:{}/{}?charset=utf8'.format(
        DIALECT,DRIVER,USERNAME,PASSWORD,HOST,PORT,DATABASE
    )

    # 绑定多个数据库
    SQLALCHEMY_BINDS = {
        'JDTracker': 'mysql+pymysql://root:cyc19971215.@127.0.0.1:3306/JDTracker?charset=utf8',
    }

    # 查询时显示sql语句
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # 设置sqlalchemy自动更跟踪数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 5

    MONGODB_SETTINGS = {
        'db': 'du',
        'host': '127.0.0.1',
        'port': 27017,
        'username': "bicycle",
        'password': "971215",
        'authentication_source': 'admin'
    }

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    pass


class ProductionConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}