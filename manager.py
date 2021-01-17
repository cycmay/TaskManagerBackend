from flask_script import Manager, Shell
from flask_migrate import Migrate,MigrateCommand

"""
flask_migrate作用：
1、通过命令的方式创建表
2、修改表的结构
"""

from app import *
from app.extensions import db

app = create_app()
manager = Manager(app)

# 第一个参数是flask实例，第二个参数SQLAlchemy实例
Migrate(app, db)

#manager是Flask-Script的实例，这条语句在flask-Script中添加一个db命令
manager.add_command("db", MigrateCommand)


if __name__ == '__main__':
    manager.run()
