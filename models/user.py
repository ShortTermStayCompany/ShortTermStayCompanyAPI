from . import db
from sqlalchemy import Column, Integer, String, CheckConstraint
#
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(80), nullable=False)
    email = db.Column(String(250), unique=True, nullable=False)
    password = db.Column(String(1280), nullable=False)
    role = db.Column(
        String(5),
        CheckConstraint("role IN ('guest', 'host', 'admin')", name='role_check'),
        nullable=False, default='guest'
    )
