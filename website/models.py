from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    balance = db.Column(db.String(10000))
    loan_amounts = db.Column(db.String(10000))
    expire_dates = db.Column(db.String(10000))
    closed = db.Column(db.Boolean)
    interests = db.Column(db.String(10000))