from . import db
from sqlalchemy import Column, Integer, String, Date, ForeignKey

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(Integer, primary_key=True, autoincrement=True)
    listing_id = db.Column(Integer, ForeignKey('listings.id'), nullable=False)
    issuer_guest_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    date_from = db.Column(Date, nullable=False)
    date_to = db.Column(Date, nullable=False)
    names_of_people = db.Column(String(250), nullable=False)
    amountOfPeople = db.Column(Integer, nullable=True)
