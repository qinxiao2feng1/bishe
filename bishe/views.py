"""
Routes and views for the flask application.
"""

from datetime import datetime
from uuid import uuid4
from flask import render_template, request, redirect, url_for, flash
from bishe import app

# -------------------------------
# 简单内存数据（重启会清空；后续可换 SQLite）
# -------------------------------
lost_items = []    # 遗失
found_items = []   # 拾到

CATEGORIES = ["证件类", "电子产品", "钥匙类", "学习用品", "衣物", "其他"]
LOCATIONS  = ["图书馆", "教学楼A", "教学楼B", "食堂", "操场", "宿舍区", "实验楼"]

# -------------------------------
# 基础页面
# -------------------------------
@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html', title='Home Page', year=datetime.now().year)

@app.route('/about')
def about():
    return render_template('about.html', title='About', year=datetime.now().year,
                           message='Your application description page.')

@app.route('/contact')
def contact():
    return render_template('contact.html', title='Contact', year=datetime.now().year,
                           message='Your contact page.')

# 可选：如果有 templates/ai_search.html，则此路由可用
@app.route('/ai')
def ai_helper():
    return render_template('ai_search.html', title='AI 도우미')

# -------------------------------
# 信息登记（GET/POST）
# -------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        item_type  = request.form.get('item_type')   # lost / found
        name       = request.form.get('name', '').strip()
        category   = request.form.get('category')
        place      = request.form.get('place')
        date       = request.form.get('date')
        contact    = request.form.get('contact', '').strip()
        description= request.form.get('description', '').strip()

        if not all([item_type, name, category, place, date]):
            flash('请完整填写所有必填字段！', 'error')
            return redirect(url_for('register'))

        item = {
            "id": str(uuid4())[:8],
            "name": name,
            "category": category,
            "place": place,
            "date": date,
            "contact": contact,
            "description": description
        }

        if item_type == 'lost':
            lost_items.append(item)
        else:
            found_items.append(item)

        flash('信息提交成功！感谢您的帮助 ❤️', 'success')
        return redirect(url_for('register'))

    return render_template('register.html', categories=CATEGORIES, locations=LOCATIONS)

# -------------------------------
# 搜索（简单关键词：名称/地点/描述）
# -------------------------------
@app.route('/search')
def search():
    keyword = (request.args.get('keyword') or '').strip().lower()
    data = (
        [dict(it, type='遗失') for it in lost_items] +
        [dict(it, type='拾到') for it in found_items]
    )

    results = []
    if keyword:
        for it in data:
            text = f"{it['name']} {it['place']} {it.get('description','')}".lower()
            if keyword in text:
                results.append(it)

    return render_template('search.html', results=results)

# -------------------------------
# 统计（与 templates/statistics.html 完全匹配）
# -------------------------------
def compute_statistics():
    total_lost  = len(lost_items)
    total_found = len(found_items)

    lost_stats  = {c: sum(1 for i in lost_items  if i["category"] == c) for c in CATEGORIES}
    found_stats = {c: sum(1 for i in found_items if i["category"] == c) for c in CATEGORIES}

    location_stats = {}
    for loc in LOCATIONS:
        l = sum(1 for i in lost_items  if i["place"] == loc)
        f = sum(1 for i in found_items if i["place"] == loc)
        if l or f:
            location_stats[loc] = {"lost": l, "found": f}

    return total_lost, total_found, lost_stats, found_stats, location_stats

@app.route('/statistics')
def statistics():
    total_lost, total_found, lost_stats, found_stats, location_stats = compute_statistics()
    return render_template(
        'statistics.html',
        total_lost=total_lost,
        total_found=total_found,
        lost_stats=lost_stats,
        found_stats=found_stats,
        location_stats=location_stats
    )