from . import db
from sqlalchemy import Column, Integer, String, Float, ForeignKey, CheckConstraint, Date

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(Integer, ForeignKey('users.id'))
    title = db.Column(String(80), nullable=True)
    numberOfPeople = db.Column(
        Integer,
        CheckConstraint('numberOfPeople >= 1 AND numberOfPeople <= 32', name='number_of_people_check'),
        nullable=False, default=1
    )
    country = db.Column(String(128), nullable=False)
    city = db.Column(String(128), nullable=False)
    price = db.Column(Float, nullable=False)
    availableFrom = db.Column(Date, nullable=False)
    availableTo = db.Column(Date, nullable=False)


    def to_dict(self):
        return {
            'id': self.id,  # Include the listing ID
            'user_id': self.user_id,
            'title': self.title,
            'numberOfPeople': self.numberOfPeople,
            'country': self.country,
            'city': self.city,
            'price': self.price,
            'availableFrom' : self.availableFrom,
            'availableTo' : self.availableTo,
        }