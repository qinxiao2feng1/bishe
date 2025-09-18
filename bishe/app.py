from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'campus_lost_found_2025'

# 内存数据存储（简化版）
lost_items = []  # 遗失物品
found_items = []  # 拾到物品

# 物品类别
CATEGORIES = ['钱包', '钥匙', '书籍', '电子产品', '其他']

# 校内地点
CAMPUS_LOCATIONS = [
    '图书馆', '食堂', '教学楼', '宿舍楼', '体育馆',
    '实验楼', '行政楼', '操场', '校门口', '停车场'
]


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """信息登记页面"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            item_type = request.form.get('item_type')  # lost 或 found
            name = request.form.get('name', '').strip()
            category = request.form.get('category')
            place = request.form.get('place')
            date_str = request.form.get('date')
            contact = request.form.get('contact', '').strip()
            description = request.form.get('description', '').strip()

            # 验证必填数据
            if not all([item_type, name, category, place, date_str]):
                flash('请填写所有必填信息！', 'error')
                return redirect(url_for('register'))

            # 验证item_type
            if item_type not in ['lost', 'found']:
                flash('请选择正确的物品状态！', 'error')
                return redirect(url_for('register'))

            # 验证类别
            if category not in CATEGORIES:
                flash('请选择正确的物品类别！', 'error')
                return redirect(url_for('register'))

            # 验证地点
            if place not in CAMPUS_LOCATIONS:
                flash('请选择正确的校园地点！', 'error')
                return redirect(url_for('register'))

            # 创建物品信息
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

            # 添加到对应列表
            if item_type == 'lost':
                lost_items.append(item_data)
                flash(f'遗失物品"{name}"信息已成功登记！', 'success')
            else:
                found_items.append(item_data)
                flash(f'拾到物品"{name}"信息已成功登记！', 'success')

            return redirect(url_for('register'))

        except Exception as e:
            print(f"Error in register: {e}")  # 调试用
            flash('信息登记时发生错误，请重试！', 'error')
            return redirect(url_for('register'))

    # GET请求，显示登记页面
    return render_template('register.html',
                           categories=CATEGORIES,
                           locations=CAMPUS_LOCATIONS)


@app.route('/search')
def search():
    """搜索与筛选页面"""
    # 获取搜索参数
    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '')
    item_type = request.args.get('type', 'all')  # all, lost, found

    # 合并所有物品数据并标记类型
    all_items = []

    if item_type in ['all', 'lost']:
        for item in lost_items:
            item_copy = item.copy()
            item_copy['type'] = '遗失物品'
            item_copy['type_class'] = 'lost'
            all_items.append(item_copy)

    if item_type in ['all', 'found']:
        for item in found_items:
            item_copy = item.copy()
            item_copy['type'] = '拾到物品'
            item_copy['type_class'] = 'found'
            all_items.append(item_copy)

    # 执行搜索过滤
    filtered_items = all_items

    if keyword:
        filtered_items = [
            item for item in filtered_items
            if keyword.lower() in item['name'].lower() or
               keyword.lower() in item['place'].lower() or
               keyword.lower() in item.get('description', '').lower()
        ]

    if category:
        filtered_items = [
            item for item in filtered_items
            if item['category'] == category
        ]

    # 按时间排序（最新的在前）
    filtered_items.sort(key=lambda x: x['created_at'], reverse=True)

    return render_template('search.html',
                           items=filtered_items,
                           categories=CATEGORIES,
                           current_keyword=keyword,
                           current_category=category,
                           current_type=item_type,
                           total_count=len(filtered_items))


@app.route('/statistics')
def statistics():
    """统计信息页面"""
    # 统计各类别物品数量
    lost_stats = {}
    found_stats = {}

    for category in CATEGORIES:
        lost_stats[category] = len([item for item in lost_items if item['category'] == category])
        found_stats[category] = len([item for item in found_items if item['category'] == category])

    # 统计各地点物品数量
    location_stats = {}
    for location in CAMPUS_LOCATIONS:
        lost_count = len([item for item in lost_items if item['place'] == location])
        found_count = len([item for item in found_items if item['place'] == location])
        if lost_count > 0 or found_count > 0:
            location_stats[location] = {'lost': lost_count, 'found': found_count}

    return render_template('statistics.html',
                           total_lost=len(lost_items),
                           total_found=len(found_items),
                           lost_stats=lost_stats,
                           found_stats=found_stats,
                           location_stats=location_stats)


@app.route('/contact')
def contact():
    """联系我们页面"""
    return render_template('contact.html')


if __name__ == '__main__':
    # 添加一些示例数据
    sample_lost = [
        {
            'id': 1,
            'name': '黑色钱包',
            'category': '钱包',
            'place': '图书馆',
            'date': '2025-09-10',
            'contact': '微信: student123',
            'description': '黑色真皮钱包，内有学生卡和少量现金',
            'created_at': '2025-09-10 14:30'
        },
        {
            'id': 2,
            'name': 'iPhone 13',
            'category': '电子产品',
            'place': '食堂',
            'date': '2025-09-11',
            'contact': '电话: 138****5678',
            'description': '蓝色iPhone 13，有保护壳',
            'created_at': '2025-09-11 12:15'
        }
    ]

    sample_found = [
        {
            'id': 3,
            'name': '一串钥匙',
            'category': '钥匙',
            'place': '教学楼',
            'date': '2025-09-12',
            'contact': '宿管处',
            'description': '蓝色钥匙扣，约5把钥匙',
            'created_at': '2025-09-12 09:20'
        }
    ]

    lost_items.extend(sample_lost)
    found_items.extend(sample_found)

    app.run(debug=True)
    from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/search')
def search():
    return render_template('search.html')

if __name__ == '__main__':
    app.run()
