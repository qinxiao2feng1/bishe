# =====================================================
# 📄 views.py — 主页面 / 物品 CRUD / AI / 统计
# =====================================================

import os
from flask import (
    Blueprint, render_template, request, redirect,
    jsonify, flash, current_app, url_for, session
)
from werkzeug.utils import secure_filename

from app import db
from app.models import LostItem, FoundItem, Feedback, User
from app.utils import CATEGORIES, LOCATIONS, statistics_data
from openai import OpenAI

# ---- 使用 auth.py 中的登录与管理员检测 ----
from app.auth import login_required, admin_required


# =====================================================
# 🔹 Blueprint
# =====================================================
views = Blueprint("views", __name__)


# =====================================================
# 🔹 首页（必须登录）
# =====================================================
@views.route("/")
@login_required
def home():

    recent_lost = LostItem.query.order_by(LostItem.id.desc()).limit(3).all()
    recent_found = FoundItem.query.order_by(FoundItem.id.desc()).limit(3).all()

    items_recent = [
        {
            "id": i.id,
            "type": "lost",
            "name": i.name,
            "category": i.category,
            "place": i.place,
            "date": i.date,
            "image": i.image,
        }
        for i in recent_lost
    ] + [
        {
            "id": i.id,
            "type": "found",
            "name": i.name,
            "category": i.category,
            "place": i.place,
            "date": i.date,
            "image": i.image,
        }
        for i in recent_found
    ]

    stats = {
        "total_items": len(recent_lost) + len(recent_found),
        "lost_items": len(recent_lost),
        "found_items": len(recent_found),
        "pending_items": len(recent_lost),
    }

    return render_template(
        "index.html",
        categories=CATEGORIES,
        locations=LOCATIONS,
        items_recent=items_recent,
        stats=stats,
    )


# =====================================================
# 🔹 保存上传文件
# =====================================================
def save_uploaded_file(file):
    if not file or file.filename == "":
        return None
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.root_path, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, filename)
    file.save(save_path)
    return "/static/uploads/" + filename


# =====================================================
# 🔹 新建失物 / 拾得物
# =====================================================
@views.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if request.method == "POST":
        item_type = request.form.get("type")
        name = request.form.get("name")
        category = request.form.get("category")
        place = request.form.get("place")
        date = request.form.get("date")
        contact = request.form.get("contact")
        description = request.form.get("description")

        image_path = save_uploaded_file(request.files.get("image"))

        if not name or not place:
            flash("필수 입력값이 누락되었습니다.", "danger")
            return redirect(url_for("views.register"))

        Model = LostItem if item_type == "lost" else FoundItem
        item = Model(
            name=name,
            category=category,
            place=place,
            date=date,
            contact=contact,
            description=description,
            image=image_path,
        )

        db.session.add(item)
        db.session.commit()
        flash("등록이 완료되었습니다!", "success")
        return redirect(url_for("views.search"))

    return render_template(
        "register.html",
        categories=CATEGORIES,
        locations=LOCATIONS
    )


# =====================================================
# 🔹 搜索页面
# =====================================================
@views.route("/search")
@login_required
def search():
    keyword = request.args.get("keyword", "")
    category = request.args.get("category", "")
    place = request.args.get("place", "")
    date = request.args.get("date", "")

    def apply_filters(query, Model):
        if keyword:
            query = query.filter(Model.name.contains(keyword))
        if category:
            query = query.filter_by(category=category)
        if place:
            query = query.filter(Model.place.contains(place))
        if date:
            query = query.filter_by(date=date)
        return query

    lost_items = apply_filters(LostItem.query, LostItem).all()
    found_items = apply_filters(FoundItem.query, FoundItem).all()

    results = [
        {
            "id": i.id,
            "type": "lost",
            "name": i.name,
            "category": i.category,
            "place": i.place,
            "date": i.date,
            "image": i.image
        }
        for i in lost_items
    ] + [
        {
            "id": i.id,
            "type": "found",
            "name": i.name,
            "category": i.category,
            "place": i.place,
            "date": i.date,
            "image": i.image
        }
        for i in found_items
    ]

    return render_template(
        "search.html",
        results=results,
        categories=CATEGORIES,
        locations=LOCATIONS,
    )


# =====================================================
# 🔹 详情页
# =====================================================
@views.route("/item/<int:item_id>")
@login_required
def item_detail(item_id):
    item = LostItem.query.get(item_id) or FoundItem.query.get(item_id)
    if not item:
        return "해당 물품을 찾을 수 없습니다.", 404

    item_type = "lost" if isinstance(item, LostItem) else "found"
    return render_template("item_detail.html", item=item, item_type=item_type)


# =====================================================
# 🔹 编辑物品
# =====================================================
@views.route("/edit/<int:item_id>", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    item = LostItem.query.get(item_id) or FoundItem.query.get(item_id)
    if not item:
        return "항목을 찾을 수 없습니다.", 404

    if request.method == "POST":
        item.name = request.form.get("name")
        item.category = request.form.get("category")
        item.place = request.form.get("place")
        item.date = request.form.get("date")
        item.contact = request.form.get("contact")
        item.description = request.form.get("description")

        new_img = save_uploaded_file(request.files.get("image"))
        if new_img:
            item.image = new_img

        db.session.commit()
        flash("수정이 완료되었습니다!", "success")
        return redirect(url_for("views.item_detail", item_id=item.id))

    return render_template("edit_item.html", item=item)


# =====================================================
# 🔹 删除物品
# =====================================================
@views.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    item = LostItem.query.get(item_id) or FoundItem.query.get(item_id)
    if not item:
        return "항목을 찾을 수 없습니다.", 404
    db.session.delete(item)
    db.session.commit()
    flash("삭제되었습니다!", "info")
    return redirect(url_for("views.search"))


# =====================================================
# 🔹 AI 问答页面
# =====================================================
@views.route("/ai", methods=["GET", "POST"])
@login_required
def ai_page():
    ai_answer = None
    if request.method == "POST":
        question = request.form.get("question", "")

        if not question:
            ai_answer = "질문이 비어 있습니다."
        else:
            try:
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "친절한 AI 분실물 도움 도우미입니다."},
                        {"role": "user", "content": question}
                    ]
                )
                ai_answer = resp.choices[0].message.content
            except Exception as e:
                ai_answer = f"오류 발생: {e}"

    return render_template("ai_search.html", ai_answer=ai_answer)


# =====================================================
# 🔹 AI 自动匹配（用于前端 fetch）
# =====================================================
@views.route("/api/ai-match", methods=["POST"])
@login_required
def ai_match():
    data = request.get_json() or {}
    user_text = data.get("description", "")

    if not user_text:
        return jsonify({"error": "설명이 비었습니다."}), 400

    def item_to_text(i, tag):
        return f"[{tag}] {i.name} / {i.category} / {i.place} / {i.date} / {i.description}\n"

    db_text = ""
    for i in LostItem.query.all():
        db_text += item_to_text(i, "분실")
    for i in FoundItem.query.all():
        db_text += item_to_text(i, "습득")

    prompt = f"""
사용자 설명: \"{user_text}\"
DB 목록:
{db_text}
가장 유사한 3개 항목을 JSON 배열 형식으로 추천해 주세요.
"""

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "AI 분실물 자동 매칭 전문가"},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({"matches": resp.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# 🔹 联系我们（用户意见 → 保存到数据库）
# =====================================================
@views.route("/contact", methods=["GET", "POST"])
@login_required
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        fb = Feedback(name=name, email=email, message=message)
        db.session.add(fb)
        db.session.commit()

        return render_template("contact.html", success=True)

    return render_template("contact.html")


# =====================================================
# 🔹 统计页面
# =====================================================
@views.route("/statistics")
@login_required
def statistics_page():
    total_lost, total_found, lost_stats, found_stats, location_stats = statistics_data()

    return render_template(
        "statistics.html",
        lost_count=total_lost,
        found_count=total_found,
        matched_count=0,
        lost_labels=list(lost_stats.keys()),
        lost_values=list(lost_stats.values()),
        found_labels=list(found_stats.keys()),
        found_values=list(found_stats.values()),
        location_stats=location_stats,
    )


# =====================================================
# 🔹 管理员后台：Dashboard
# =====================================================
@views.route("/admin/dashboard")
@admin_required
def admin_dashboard():

    users = User.query.all()
    return render_template("admin_dashboard.html", users=users)
# =====================================================
# 🔹 管理员后台：查看用户留言
# =====================================================
@views.route("/admin/messages")
@admin_required
def admin_messages():
    messages = Feedback.query.order_by(Feedback.id.desc()).all()
    return render_template("admin_messages.html", messages=messages)
