# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # ====== 基本配置 ======
    app.config["SECRET_KEY"] = "your-secret-key"
    app.config["SESSION_PERMANENT"] = False

    db_path = os.path.join(app.root_path, "lostfound.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # 初始化数据库
    db.init_app(app)

    # ====== 导入蓝图（非常重要，避免循环引用）======
    from .views import views                 # 主页/物品 CRUD
    from .auth import auth_bp                # 登录注册
    from .admin import admin_bp              # 管理员面板（如存在）
    from .ai_match import ai_bp              # AI 自动匹配（API）

    # 导入 models（确保 SQLAlchemy 识别所有表）
    from . import models

    # ====== 注册蓝图 ======
    app.register_blueprint(views)                     # 无前缀 → "/" 开头路由
    app.register_blueprint(auth_bp, url_prefix="/auth")   # 所有 auth 路由自动变成 /auth/xxx
    app.register_blueprint(admin_bp, url_prefix="/admin") # 管理后台
    app.register_blueprint(ai_bp, url_prefix="/ai")       # AI API → /ai/xxx

    # ====== 自动建表 ======
    with app.app_context():
        db.create_all()

    return app
