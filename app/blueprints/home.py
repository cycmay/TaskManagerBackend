from flask import render_template, Blueprint, current_app, make_response, jsonify

from app.extensions import db

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def index():
    return render_template('index.html')
    