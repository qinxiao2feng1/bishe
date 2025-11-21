# app/models.py
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# =====================================
# 用户表
# =====================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 关联：用户 → 发布的失物
    lost_items = db.relationship("LostItem", backref="user", lazy=True)

    # 🔗 关联：用户 → 发布的拾得物
    found_items = db.relationship("FoundItem", backref="user", lazy=True)

    # 设置密码
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # 校验密码
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
        }


# =====================================
# 失物表
# =====================================
class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255))
    place = db.Column(db.String(255))
    date = db.Column(db.String(255))
    contact = db.Column(db.String(255))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔑 外键：物品属于谁
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)


# =====================================
# 拾得物表
# =====================================
class FoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255))
    place = db.Column(db.String(255))
    date = db.Column(db.String(255))
    contact = db.Column(db.String(255))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔑 外键：物品属于谁
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=db.func.now())
