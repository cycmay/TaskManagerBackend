import pymongo

from app.configd.conf import mongo as mongo_conf

Gaze = "Gaze"
JDCollection = "JDTask"


class MongoSession(object):

    def __init__(self, db=Gaze, col=JDCollection):
        """

        :param col: collection
        """
        self.dbClient = pymongo.MongoClient(
            "mongodb://" + mongo_conf['user'] + ':' + mongo_conf['passwd'] + '@' + mongo_conf['host'] + ':' + str(
                mongo_conf['port']))
        self.db = self.dbClient[db]
        self.col = self.db[col]

    def create(self, item: dict):
        return self.col.insert_one(item)

    def read(self):
        """
        查询所有数据
        :return:
        """
        return self.col.find()

    def update(self, where:dict, item:dict):
        ret = self.col.find_one(where)
        if not ret:
            return False
        print(item)
        return self.col.update_one(where, item)

    def delete(self, where:dict):
        return self.col.delete_one(where)

    # 事务处理func
    def transaction(self, func):

        def wrapper(*args, **kwargs):

            session = self.dbClient.start_session()
            session.start_transaction()
            try:
                func(*args, **kwargs)
            except:
                # 操作异常，中断事务
                session.abort_transaction()
            else:
                session.commit_transaction()
            finally:
                session.end_session()

        return wrapper


