from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from Decorators.decorators import require_role
from models import db, Booking, listingBookedDates
from datetime import datetime, timedelta

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/insert_booking', methods=['POST'])
@jwt_required()
@require_role('user')
def insert_booking():

    current_user_id = get_jwt_identity()

    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'message': 'User ID is required'}), 400
    if 'listing_id' not in data:
        return jsonify({'message': 'Listing ID is required'}), 400

    required_fields = ['dateFrom', 'dateTo', 'namesOfPeople']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    ## bookingModel

    # Check for overlapping bookings
    existing_bookings = db.session.query(Booking).filter(
        Booking.listing_id == data['listing_id']
    ).all()

    data['dateFrom'] = datetime.strptime(data['dateFrom'], '%Y-%m-%d').date()
    data['dateTo'] = datetime.strptime(data['dateTo'], '%Y-%m-%d').date()

    for booking in existing_bookings:
        if (data['dateFrom'] <= booking.date_to) and (data['dateTo'] >= booking.date_from):
            return jsonify({'message': 'Booking already exists on selected dates'}), 400

    new_booking = Booking(
        listing_id=data['listing_id'],
        issuer_guest_id=data['user_id'],
        date_from=data['dateFrom'],
        date_to=data['dateTo'],
        names_of_people=data['namesOfPeople'],
        amountOfPeople=data.get('amountOfPeople', 1)
    )

    db.session.add(new_booking)


    ## listingBookedDatesModel
    bookStartDate = data['dateFrom']
    bookEndDate = data['dateTo']
    Dates = []
    # Generate all dates between bookStartDate and bookEndDate

    while bookStartDate <= bookEndDate: # Include end date
        Dates.append(bookStartDate)
        bookStartDate += timedelta(days=1)

    print(Dates)

    # Insert dates into listingBookedDates table

    bookedDatesbyListing = []
    for date in Dates:
        bookedDatesbyListing.append(Booking(
            listing_id=data['listing_id'],
            booked_date=date
        ))
    db.session.add_all(bookedDatesbyListing)

    db.session.commit()
    return jsonify({'message': 'Booking inserted successfully'}), 201
