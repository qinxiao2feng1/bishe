# app/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from app.models import User, LostItem, FoundItem, Feedback   
from app import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ============================ 관리자 권한 체크 ============================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("관리자 권한이 필요합니다.", "danger")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return wrapper

# ============================ 관리자 대시보드 ============================
@admin_bp.route("/", methods=["GET"])
@admin_required
def dashboard():
    total_users = User.query.count()
    total_lost = LostItem.query.count()
    total_found = FoundItem.query.count()
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    recent_lost = LostItem.query.order_by(LostItem.id.desc()).limit(5).all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_lost=total_lost,
        total_found=total_found,
        recent_users=recent_users,
        recent_lost=recent_lost
    )

# ============================ 사용자 리스트 ============================
@admin_bp.route("/users", methods=["GET"])
@admin_required
def users():
    q = request.args.get("q", "").strip()
    if q:
        users = User.query.filter(User.username.contains(q)).all()
    else:
        users = User.query.order_by(User.id.desc()).all()

    return render_template("admin_users.html", users=users, q=q)

# ============================ 관리자 권한 토글 ============================
@admin_bp.route("/users/<int:user_id>/toggle_admin", methods=["POST"])
@admin_required
def toggle_admin(user_id):
    if session.get("user_id") == user_id:
        return jsonify({"error": "자기 자신 권한 변경은 불가능합니다."}), 400

    u = User.query.get_or_404(user_id)
    u.is_admin = not u.is_admin
    db.session.commit()

    return jsonify({"ok": True, "is_admin": u.is_admin})

# ============================ 사용자 삭제 ============================
@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    if session.get("user_id") == user_id:
        return jsonify({"error": "자기 자신은 삭제할 수 없습니다."}), 400

    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()

    return jsonify({"ok": True})

# ============================ 물품 관리 ============================
@admin_bp.route("/items", methods=["GET"])
@admin_required
def items():
    t = request.args.get("type", "all")

    if t == "lost":
        items = LostItem.query.order_by(LostItem.id.desc()).all()
        return render_template("admin_items.html", items=items, type="lost")

    elif t == "found":
        items = FoundItem.query.order_by(FoundItem.id.desc()).all()
        return render_template("admin_items.html", items=items, type="found")

    else:
        lost = LostItem.query.order_by(LostItem.id.desc()).all()
        found = FoundItem.query.order_by(FoundItem.id.desc()).all()

        return render_template(
            "admin_items.html",
            items={"lost": lost, "found": found},
            type="all"
        )

# ============================ 물품 삭제 ============================
@admin_bp.route("/items/<string:item_type>/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_item(item_type, item_id):
    if item_type == "lost":
        item = LostItem.query.get_or_404(item_id)
    else:
        item = FoundItem.query.get_or_404(item_id)

    db.session.delete(item)
    db.session.commit()

    return jsonify({"ok": True})

# ============================ 물품 resolved 토글 ============================
@admin_bp.route("/items/<string:item_type>/<int:item_id>/toggle_resolved", methods=["POST"])
@admin_required
def toggle_resolved(item_type, item_id):
    Model = LostItem if item_type == "lost" else FoundItem
    item = Model.query.get_or_404(item_id)

    if hasattr(item, "resolved"):
        item.resolved = not item.resolved
        db.session.commit()
        return jsonify({"ok": True, "resolved": item.resolved})
    else:
        return jsonify({"error": "모델에 resolved 필드가 없습니다."}), 400

# ============================ 시스템 통계 ============================
@admin_bp.route("/stats")
@admin_required
def stats():
    total_users = User.query.count()
    total_lost = LostItem.query.count()
    total_found = FoundItem.query.count()
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    recent_lost = LostItem.query.order_by(LostItem.id.desc()).limit(5).all()

    return render_template(
        "admin_stats.html",
        total_users=total_users,
        total_lost=total_lost,
        total_found=total_found,
        recent_users=recent_users,
        recent_lost=recent_lost
    )

# ============================ 사용자 피드백 관리 ============================
@admin_bp.route("/feedback")
@admin_required
def admin_feedback():
    feedbacks = Feedback.query.order_by(Feedback.id.desc()).all()
    return render_template("admin_feedback.html", feedbacks=feedbacks)
