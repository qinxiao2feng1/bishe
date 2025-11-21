from flask import Blueprint, request, jsonify, session, render_template, redirect
from app import db
from app.models import User
from functools import wraps

auth_bp = Blueprint('auth', __name__)


# =======================
# 🔹 登录强制检查
# =======================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/auth/login")
        return f(*args, **kwargs)
    return wrapper


# =======================
# 🔹 注册页面
# =======================
@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template("register_user.html")


# =======================
# 🔹 登录页面
# =======================
@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template("login.html")


# =======================
# 🔹 注册 API
# =======================
@auth_bp.route('/api/register', methods=['POST'])
def register_api():
    data = request.json
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    is_admin = bool(data.get('is_admin', False))

    if not username or not password:
        return jsonify({"error": "아이디와 비밀번호를 입력하세요"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "이미 존재하는 사용자입니다"}), 400

    user = User(username=username, is_admin=is_admin)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "회원가입 성공"})


# =======================
# 🔹 登录 API（已修改 session.permanent=False）
# =======================
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "아이디 또는 비밀번호가 틀립니다"}), 401

    # 浏览器关闭即失效
    session.permanent = False

    session['user_id'] = user.id
    session['username'] = user.username
    session['is_admin'] = user.is_admin

    return jsonify({"message": "로그인 성공", "is_admin": user.is_admin})


# =======================
# 🔹 Logout
# =======================
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "로그아웃 되었습니다"})


# =======================
# 🔹 当前用户
# =======================
@auth_bp.route('/api/me', methods=['GET'])
def me():
    if 'user_id' not in session:
        return jsonify({"user": None})
    return jsonify({
        "user": {
            "id": session['user_id'],
            "username": session.get('username'),
            "is_admin": session.get('is_admin')
        }
    })


# =======================
# 🔹 管理员登录页面
# =======================
@auth_bp.route('/admin/login', methods=['GET'])
def admin_login_page():
    return render_template("admin_login.html")


# =======================
# 🔹 管理员登录 API（加入 session.permanent=False）
# =======================
@auth_bp.route('/api/admin/login', methods=['POST'])
def admin_login_api():
    data = request.json
    username = data.get("username", "")
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "아이디 또는 비밀번호가 틀립니다"}), 401

    if not user.is_admin:
        return jsonify({"error": "관리자 권한이 없습니다"}), 403

    # 管理员也不能保持登录
    session.permanent = False

    session["user_id"] = user.id
    session["username"] = user.username
    session["is_admin"] = True

    return jsonify({"message": "관리자 로그인 성공"})


# =======================
# 🔹 管理员权限
# =======================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/auth/login")
        if not session.get("is_admin"):
            return redirect("/")
        return f(*args, **kwargs)
    return wrapper
