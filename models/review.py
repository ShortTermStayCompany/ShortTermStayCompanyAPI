from . import db
from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    stay_id = db.Column(Integer, ForeignKey('bookings.id'), nullable=False)
    guest_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = db.Column(Integer, nullable=False)
    comment = db.Column(String(500))
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_between_1_and_5'),
    )
