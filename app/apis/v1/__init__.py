from flask import Blueprint


api_v1 = Blueprint('api_v1', __name__)

from app.apis.v1 import resources
from app.apis.v1 import buyitem
from app.apis.v1 import monitorTask
from app.apis.v1 import product
from app.apis.v1 import productActivity