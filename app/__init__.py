import os
from flask import Flask

import click

from app import views, models
from app.extensions import db, csrf, mongodb_du
from app.settings import config

from app.apis.v1 import api_v1
from app.blueprints.home import home_bp
from app.blueprints.buyitems import buyitems_bp

from flask_cors import CORS

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)

    return app



def register_extensions(app):
    db.init_app(app)
    mongodb_du.init_app(app)
    csrf.init_app(app)

def register_blueprints(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(buyitems_bp)
    app.register_blueprint(api_v1, url_prefix='/api/v1')

def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    # @app.cli.command()
    # @click.option()
    # def migrate():
    #     """Initialize the database."""
    #     if drop:
    #         click.confirm('This operation will delete the database, do you want to continue?', abort=True)
    #         db.drop_all()
    #         click.echo('Drop tables.')
    #     db.create_all()
    #     click.echo('Initialized database.')

    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass