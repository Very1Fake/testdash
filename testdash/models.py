from Crypto.Hash import SHA512
from flask_login import UserMixin

from . import login_manager
from . import db


@login_manager.user_loader
def load_user(user_id):  # User load function for login manager
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):  # User model
    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True, nullable=False)
    login = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), unique=True, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False, default=-1)

    def __repr__(self):
        return f"User ('{self.id}', '{self.login}')"


class Action(db.Model):  # Temporary unused
    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True, nullable=False)
    name = db.Column(db.String(32), nullable=False)
    login = db.Column(db.String(64), nullable=False)
    comment = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"Action ('{self.id}', '{self.name}', '{self.login}')"


class Visit(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True, autoincrement=True, nullable=False)
    login = db.Column(db.String(64), nullable=False)
    address = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Visit ('{self.id}', '{self.login}', '{self.address}')"
