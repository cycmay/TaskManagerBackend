import redis
from app.configd.conf import redis as redis_conf


class RedisSession(object):
    def __init__(self):
        self.pool = redis.ConnectionPool(host=redis_conf["host"], port=redis_conf["port"], decode_responses=True)
        self.r = redis.Redis(connection_pool=self.pool)

    def set(self, key, value):
        return self.r.set(key, value)

    def get(self, key):
        return self.r.get(key)

    def sAdd(self, set_key, item):
        return self.r.sadd(set_key, item)

    def sList(self, set_key):
        return self.r.smembers(set_key)

    def sRemove(self, set_key, item):
        return self.r.srem(set_key, item)

    def hSet(self, hash_key, key, value):
        return self.r.hset(hash_key, key, value)

    def hGet(self, hash_key, key):
        return self.r.hget(hash_key, key)

    def hRemove(self, hash_key, key):
        return self.r.hdel(hash_key, key)