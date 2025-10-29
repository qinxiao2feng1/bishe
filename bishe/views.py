from flask import render_template, request, redirect, url_for, flash
from datetime import datetime
from bishe import app
from bishe.models import init_db, add_item, search_items, statistics_data

CATEGORIES = ["지갑", "열쇠", "책", "전자제품", "의류", "기타"]
LOCATIONS = ["도서관", "식당", "강의동", "기숙사", "운동장", "실험실", "행정동"]

# 앱 실행 시 DB 초기화
with app.app_context():
    init_db()


@app.route('/')
def home():
    return render_template("index.html")

@app.route('/ai')
def ai_helper():
    return render_template("ai_search.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        item_type = request.form.get('item_type')
        data = {
            "item_type": item_type,
            "name": request.form.get('name'),
            "category": request.form.get('category'),
            "place": request.form.get('place'),
            "date": request.form.get('date'),
            "contact": request.form.get('contact'),
            "description": request.form.get('description')
        }

        add_item(data)
        flash("✅ 등록이 완료되었습니다!", "success")
        return redirect(url_for('register'))

    return render_template("register.html", categories=CATEGORIES, locations=LOCATIONS)

@app.route('/search')
def search():
    keyword = request.args.get("keyword", "")
    category = request.args.get("category", "")
    item_type = request.args.get("type", "all")
    items = search_items(keyword, category, item_type)

    return render_template("search.html",
                           items=items,
                           categories=CATEGORIES,
                           current_keyword=keyword,
                           current_category=category,
                           current_type=item_type,
                           total_count=len(items))

@app.route('/statistics')
def statistics():
    total_lost, total_found, lost_stats, found_stats, location_stats = statistics_data(CATEGORIES, LOCATIONS)
    return render_template("statistics.html",
                           total_lost=total_lost,
                           total_found=total_found,
                           lost_stats=lost_stats,
                           found_stats=found_stats,
                           location_stats=location_stats)
