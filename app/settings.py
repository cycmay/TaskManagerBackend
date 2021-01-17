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

    SQLALCHEMY_DATABASE_URI = '{}+{}://{}:{}@{}:{}/{}?charset=utf8'.format(
        DIALECT,DRIVER,USERNAME,PASSWORD,HOST,PORT,DATABASE
    )
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
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