# =====================================================
# 📄 views.py — Flask 라우트 (페이지/기능 정의)
# =====================================================

import os
from flask import (
    Blueprint, render_template, request, redirect,
    jsonify, flash, current_app, url_for
)
from werkzeug.utils import secure_filename

from . import db
from .models import LostItem, FoundItem
from .utils import CATEGORIES, LOCATIONS, statistics_data

from openai import OpenAI

# 🔹 Blueprint 생성
views = Blueprint("views", __name__)


# =====================================================
# 🔹 메인 페이지 (최근 등록된 분실물/습득물 요약)
# =====================================================
@views.route("/")
def index():
    # 최근 분실물 / 습득물 3개씩 조회
    recent_lost = LostItem.query.order_by(LostItem.id.desc()).limit(3).all()
    recent_found = FoundItem.query.order_by(FoundItem.id.desc()).limit(3).all()

    items_recent = []

    # 분실물
    for i in recent_lost:
        items_recent.append({
            "id": i.id,
            "type": "lost",
            "name": i.name,
            "category": i.category,
            "place": i.place,
            "date": i.date,
            "image": i.image
        })

    # 습득물
    for i in recent_found:
        items_recent.append({
            "id": i.id,
            "type": "found",
            "name": i.name,
            "category": i.category,
            "place": i.place,
            "date": i.date,
            "image": i.image
        })

    # 간단 통계 (메인 화면용)
    stats = {
        "total_items": len(recent_lost) + len(recent_found),
        "lost_items": len(recent_lost),
        "found_items": len(recent_found),
        "pending_items": len(recent_lost),   # 아직 찾지 못한 분실물 수 정도로 사용
    }

    return render_template(
        "index.html",
        categories=CATEGORIES,
        locations=LOCATIONS,
        items_recent=items_recent,
        stats=stats
    )


# =====================================================
# 🔹 등록 페이지 (분실물 / 습득물 + 이미지 업로드)
# =====================================================
@views.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        item_type = request.form.get("type")      # lost / found
        name = request.form.get("name")
        category = request.form.get("category")
        place = request.form.get("place")
        date = request.form.get("date")
        contact = request.form.get("contact")
        description = request.form.get("description")

        # ---- 이미지 업로드 처리 ----
        image_file = request.files.get("image")
        image_path = None

        if image_file and image_file.filename != "":
            filename = secure_filename(image_file.filename)

            # app/static/uploads 경로 생성
            upload_dir = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            save_path = os.path.join(upload_dir, filename)
            image_file.save(save_path)

            # 웹에서 접근 가능한 경로 (/static/...)
            image_path = "/static/uploads/" + filename

        # ---- 필수 입력값 체크 ----
        if not name or not place:
            flash("필수 입력값이 누락되었습니다.", "danger")
            return redirect(url_for("views.register"))

        # ---- DB 저장 ----
        if item_type == "lost":
            item = LostItem(
                name=name,
                category=category,
                place=place,
                date=date,
                contact=contact,
                description=description,
                image=image_path
            )
        elif item_type == "found":
            item = FoundItem(
                name=name,
                category=category,
                place=place,
                date=date,
                contact=contact,
                description=description,
                image=image_path
            )
        else:
            flash("등록 유형(lost / found)에 오류가 있습니다.", "danger")
            return redirect(url_for("views.register"))

        db.session.add(item)
        db.session.commit()

        flash("등록이 완료되었습니다!", "success")
        return redirect(url_for("views.search"))

    # GET 요청 시 등록 폼 렌더링
    return render_template(
        "register.html",
        categories=CATEGORIES,
        locations=LOCATIONS
    )


# =====================================================
# 🔹 검색 페이지 (소형 카드 + 수정/삭제 버튼)
# =====================================================
@views.route("/search")
def search():
    keyword = request.args.get("keyword", "")
    category = request.args.get("category", "")
    place = request.args.get("place", "")
    date = request.args.get("date", "")

    lost_q = LostItem.query
    found_q = FoundItem.query

    # ---- 키워드 검색 (이름 기준) ----
    if keyword:
        lost_q = lost_q.filter(LostItem.name.contains(keyword))
        found_q = found_q.filter(FoundItem.name.contains(keyword))

    # ---- 카테고리 필터 ----
    if category:
        lost_q = lost_q.filter_by(category=category)
        found_q = found_q.filter_by(category=category)

    # ---- 장소 필터 ----
    if place:
        lost_q = lost_q.filter(LostItem.place.contains(place))
        found_q = found_q.filter(FoundItem.place.contains(place))

    # ---- 날짜 필터 (문자열 동일 비교) ----
    if date:
        lost_q = lost_q.filter_by(date=date)
        found_q = found_q.filter_by(date=date)

    # ---- 분실/습득 리스트 합치기 (템플릿에서 results 사용) ----
    results = []

    for i in lost_q.all():
        results.append({
            "id": i.id,
            "type": "lost",
            "name": i.name,
            "category": i.category,
            "place": i.place,
            "date": i.date,
            "image": i.image
        })

    for i in found_q.all():
        results.append({
            "id": i.id,
            "type": "found",
            "name": i.name,
            "category": i.category,
            "place": i.place,
            "date": i.date,
            "image": i.image
        })

    return render_template(
        "search.html",
        results=results,             # 🔸 search.html 에서 results 루프 사용
        categories=CATEGORIES,
        locations=LOCATIONS
    )


# =====================================================
# 🔹 상세 페이지 (분실/습득 공용)
# =====================================================
@views.route("/item/<int:item_id>")
def item_detail(item_id):
    item = LostItem.query.get(item_id)
    item_type = "lost"

    if not item:
        item = FoundItem.query.get(item_id)
        item_type = "found"

    if not item:
        return "해당 물품을 찾을 수 없습니다.", 404

    return render_template(
        "item_detail.html",   # 또는 detail.html, 프로젝트에 맞게 수정
        item=item,
        item_type=item_type
    )


# =====================================================
# 🔹 수정 페이지 (GET + POST, 이미지 수정 포함)
# =====================================================
@views.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    # 분실물/습득물 중 하나 찾기
    item = LostItem.query.get(item_id) or FoundItem.query.get(item_id)
    if not item:
        return "항목을 찾을 수 없습니다.", 404

    if request.method == "POST":
        # ---- 폼 데이터 반영 ----
        item.name = request.form.get("name")
        item.category = request.form.get("category")
        item.place = request.form.get("place")
        item.date = request.form.get("date")
        item.contact = request.form.get("contact")
        item.description = request.form.get("description")

        # ---- 새 이미지 업로드 시 교체 ----
        new_img = request.files.get("image")
        if new_img and new_img.filename != "":
            filename = secure_filename(new_img.filename)

            upload_dir = os.path.join(current_app.root_path, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            save_path = os.path.join(upload_dir, filename)
            new_img.save(save_path)

            item.image = "/static/uploads/" + filename

        db.session.commit()
        flash("수정이 완료되었습니다!", "success")
        return redirect(url_for("views.item_detail", item_id=item.id))

    # GET 요청 시 수정 페이지 렌더링
    return render_template("edit_item.html", item=item)


# =====================================================
# 🔹 삭제 기능 (소카드에서 🗑 버튼 눌렀을 때)
# =====================================================
@views.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    item = LostItem.query.get(item_id) or FoundItem.query.get(item_id)
    if not item:
        return "항목을 찾을 수 없습니다.", 404

    db.session.delete(item)
    db.session.commit()
    flash("삭제되었습니다!", "info")
    return redirect(url_for("views.search"))


# =====================================================
# 🔹 AI 검색 페이지 (단순 폼 + 결과 표시)
# =====================================================
@views.route("/ai", methods=["GET", "POST"])
def ai_page():
    ai_answer = None

    if request.method == "POST":
        question = request.form.get("question", "")
        if not question:
            ai_answer = "질문이 비어 있습니다."
        else:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            try:
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
# 🔹 일반 챗봇 API (프론트에서 fetch 로 호출할 수 있는 형태)
# =====================================================
@views.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "")

    if not message:
        return jsonify({"error": "메시지가 비었습니다."}), 400

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "친절한 AI 분실물 안내 도우미입니다."},
                {"role": "user", "content": message}
            ]
        )
        answer = resp.choices[0].message.content
        return jsonify({"message": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================
# 🔹 AI 자동 매칭 API (DB 내용과 비교해 유사 항목 추천)
# =====================================================
@views.route("/api/ai-match", methods=["POST"])
def ai_match():
    data = request.get_json() or {}
    user_text = data.get("description", "")

    if not user_text:
        return jsonify({"error": "설명이 비었습니다."}), 400

    lost_items = LostItem.query.all()
    found_items = FoundItem.query.all()

    # DB 텍스트 정리
    db_text = ""
    for i in lost_items:
        db_text += f"[분실] {i.name} / {i.category} / {i.place} / {i.date} / {i.description}\n"
    for i in found_items:
        db_text += f"[습득] {i.name} / {i.category} / {i.place} / {i.date} / {i.description}\n"

    prompt = f"""
사용자 설명: \"{user_text}\"
DB 목록:
{db_text}
가장 유사한 3개 항목을 JSON 배열 형식으로 추천해 주세요.
"""

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
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
# 🔹 문의 페이지
# =====================================================
@views.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("문의가 성공적으로 접수되었습니다!", "success")
        return redirect(url_for("views.contact"))
    return render_template("contact.html")


# =====================================================
# 🔹 통계 페이지
# =====================================================
@views.route("/statistics")
def statistics_page():
    # app.utils.statistics_data() 사용
    total_lost, total_found, lost_stats, found_stats, location_stats = statistics_data()

    lost_labels = list(lost_stats.keys())
    lost_values = list(lost_stats.values())

    found_labels = list(found_stats.keys())
    found_values = list(found_stats.values())

    return render_template(
        "statistics.html",
        lost_count=total_lost,
        found_count=total_found,
        matched_count=0,      # 추후 매칭 기능 연동 가능
        lost_labels=lost_labels,
        lost_values=lost_values,
        found_labels=found_labels,
        found_values=found_values,
        location_stats=location_stats
    )
