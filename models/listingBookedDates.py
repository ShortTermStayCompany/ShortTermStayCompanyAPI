from . import db
from sqlalchemy import Column, Integer, String, Float, ForeignKey, CheckConstraint, Date, PrimaryKeyConstraint


class Listing(db.Model):
    __tablename__ = 'listingBookedDates'
    # id = db.Column(Integer, primary_key=True, autoincrement=True)
    listing_id = db.Column(Integer, ForeignKey('listings.id'))
    booked_date = db.Column(Date, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint('listing_id', 'booked_date'),
    )


