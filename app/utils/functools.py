import json
import random
import re
import sys
import csv

DEFAULT_TIMEOUT = 10

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'

USER_AGENTS = [

]
with open('app/utils/UA/ua_string.csv', 'r', encoding='unicode_escape') as f:
    reader = csv.reader(f)
    count = 0
    for row in reader:
        if(count>=40000):
            break
        USER_AGENTS.append(row[0])
        count += 1


def parse_json(s):
    begin = s.find('{')
    end = s.rfind('}') + 1
    if begin < 0 or end < 0:
        return {}
    else:
        try:
            return json.loads(s[begin:end])
        except:
            print("json:", s)
            print("Unexpected error:", sys.exc_info())
            return {}


def get_random_useragent():
    """生成随机的UserAgent
    :return: UserAgent字符串
    """
    return random.choice(USER_AGENTS)


def parse_area_id(area):
    """解析地区id字符串：将分隔符替换为下划线 _
    :param area: 地区id字符串（使用 _ 或 - 进行分割），如 12_904_3375 或 12-904-3375
    :return: 解析后字符串
    """
    area_id_list = list(map(lambda x: x.strip(), re.split('_|-', area)))
    area_id_list.extend((4 - len(area_id_list)) * ['0'])
    return '_'.join(area_id_list)
