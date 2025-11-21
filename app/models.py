from app import db

class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255))
    place = db.Column(db.String(255))
    date = db.Column(db.String(255))
    contact = db.Column(db.String(255))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))


class FoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255))
    place = db.Column(db.String(255))
    date = db.Column(db.String(255))
    contact = db.Column(db.String(255))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
