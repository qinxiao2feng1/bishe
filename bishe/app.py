from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'campus_lost_found_2025'

# 메모리 데이터 저장 (임시)
lost_items = []   # 분실물
found_items = []  # 습득물

# 물품 카테고리
CATEGORIES = ['지갑', '열쇠', '책', '전자제품', '기타']

# 캠퍼스 위치
CAMPUS_LOCATIONS = [
    '도서관', '식당', '강의동', '기숙사', '체육관',
    '실험동', '행정동', '운동장', '정문', '주차장'
]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """정보 등록 페이지"""
    if request.method == 'POST':
        try:
            item_type = request.form.get('item_type')  # lost / found
            name = request.form.get('name', '').strip()
            category = request.form.get('category')
            place = request.form.get('place')
            date_str = request.form.get('date')
            contact = request.form.get('contact', '').strip()
            description = request.form.get('description', '').strip()

            # 필수 입력 확인
            if not all([item_type, name, category, place, date_str]):
                flash('⚠️ 필수 항목을 모두 입력해주세요.', 'error')
                return redirect(url_for('register'))

            if item_type not in ['lost', 'found']:
                flash('물품 상태를 선택해주세요.', 'error')
                return redirect(url_for('register'))

            if category not in CATEGORIES:
                flash('올바른 물품 종류를 선택해주세요.', 'error')
                return redirect(url_for('register'))

            if place not in CAMPUS_LOCATIONS:
                flash('올바른 위치를 선택해주세요.', 'error')
                return redirect(url_for('register'))

            item_data = {
                'id': len(lost_items) + len(found_items) + 1,
                'name': name,
                'category': category,
                'place': place,
                'date': date_str,
                'contact': contact,
                'description': description,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M')
            }

            if item_type == 'lost':
                lost_items.append(item_data)
                flash(f'🔍 분실물 "{name}" 정보가 성공적으로 등록되었습니다!', 'success')
            else:
                found_items.append(item_data)
                flash(f'📦 습득물 "{name}" 정보가 성공적으로 등록되었습니다!', 'success')

            return redirect(url_for('register'))

        except Exception as e:
            print(f"[ERROR] register: {e}")
            flash('등록 중 오류가 발생했습니다. 다시 시도해주세요.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html',
                           categories=CATEGORIES,
                           locations=CAMPUS_LOCATIONS)


@app.route('/search')
def search():
    """검색 페이지"""
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '')
    item_type = request.args.get('type', 'all')

    result_items = []

    if item_type in ['all', 'lost']:
        for item in lost_items:
            obj = item.copy()
            obj['type'] = '분실물'
            obj['type_class'] = 'lost'
            result_items.append(obj)

    if item_type in ['all', 'found']:
        for item in found_items:
            obj = item.copy()
            obj['type'] = '습득물'
            obj['type_class'] = 'found'
            result_items.append(obj)

    if keyword:
        result_items = [
            i for i in result_items
            if keyword.lower() in i['name'].lower()
            or keyword.lower() in i['place'].lower()
            or keyword.lower() in i.get('description', '').lower()
        ]

    if category:
        result_items = [i for i in result_items if i['category'] == category]

    result_items.sort(key=lambda x: x['created_at'], reverse=True)

    return render_template('search.html',
                           items=result_items,
                           categories=CATEGORIES,
                           current_keyword=keyword,
                           current_category=category,
                           current_type=item_type,
                           total_count=len(result_items))


@app.route('/statistics')
def statistics():
    """통계 페이지"""
    lost_stats = {c: len([i for i in lost_items if i['category'] == c]) for c in CATEGORIES}
    found_stats = {c: len([i for i in found_items if i['category'] == c]) for c in CATEGORIES}

    location_stats = {}
    for loc in CAMPUS_LOCATIONS:
        l = len([i for i in lost_items if i['place'] == loc])
        f = len([i for i in found_items if i['place'] == loc])
        if l or f:
            location_stats[loc] = {'lost': l, 'found': f}

    return render_template('statistics.html',
                           total_lost=len(lost_items),
                           total_found=len(found_items),
                           lost_stats=lost_stats,
                           found_stats=found_stats,
                           location_stats=location_stats)


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
