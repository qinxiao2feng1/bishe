# app/__init__.py
# ==========================================
# 🔧 Flask 앱 초기화
# ==========================================
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# ✅ 전역에서 딱 1번만 생성
db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    # 기본 설정
    app.config["SECRET_KEY"] = "your-secret-key"

    # DB 경로 (프로젝트 안에 lostfound.db 생성)
    db_path = os.path.join(app.root_path, "lostfound.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ✅ 이 app 과 db 를 연결
    db.init_app(app)

    # Blueprint 등록
    from .views import views
    app.register_blueprint(views)

    # 테이블 생성
    with app.app_context():
        from . import models   # <-- 모델을 여기서 import
        db.create_all()

    return app
