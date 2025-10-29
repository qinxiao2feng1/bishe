from bishe import db
from datetime import datetime

class LostFoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_type = db.Column(db.String(10), nullable=False)  # lost / found
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    place = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    contact = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

def init_db():
    db.create_all()

def add_item(data):
    item = LostFoundItem(**data)
    db.session.add(item)
    db.session.commit()

def search_items(keyword="", category="", item_type="all"):
    query = LostFoundItem.query

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (LostFoundItem.name.like(like)) |
            (LostFoundItem.place.like(like)) |
            (LostFoundItem.description.like(like))
        )
    if category:
        query = query.filter_by(category=category)
    if item_type in ["lost", "found"]:
        query = query.filter_by(item_type=item_type)

    return query.order_by(LostFoundItem.created_at.desc()).all()

def statistics_data(categories, locations):
    data = LostFoundItem.query.all()
    total_lost = sum(1 for i in data if i.item_type == 'lost')
    total_found = sum(1 for i in data if i.item_type == 'found')

    lost_stats = {c: sum(1 for i in data if i.category == c and i.item_type == 'lost') for c in categories}
    found_stats = {c: sum(1 for i in data if i.category == c and i.item_type == 'found') for c in categories}

    location_stats = {}
    for loc in locations:
        l = sum(1 for i in data if i.place == loc and i.item_type == 'lost')
        f = sum(1 for i in data if i.place == loc and i.item_type == 'found')
        if l or f:
            location_stats[loc] = {"lost": l, "found": f}

    return total_lost, total_found, lost_stats, found_stats, location_stats
