from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from Decorators.decorators import require_role
from models import db, Booking, ListingBookedDates
from datetime import datetime, timedelta

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/insert_booking', methods=['POST'])
@jwt_required()
@require_role('guest')
def insert_booking():

    current_user_id = get_jwt_identity()

    data = request.get_json()
    required_fields = ['listing_id','dateFrom', 'dateTo', 'namesOfPeople']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return jsonify({'message': f'Missing required fields: {",".join(missing_fields)}'}), 400
    try:
        data['dateFrom'] = datetime.strptime(data['dateFrom'], '%Y-%m-%d').date()
        data['dateTo'] = datetime.strptime(data['dateTo'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    ## bookingModel

    # Check for overlapping bookings

    existing_bookings = db.session.query(Booking).filter(
        Booking.listing_id == data['listing_id']
    ).all()

    for booking in existing_bookings:
        if (data['dateFrom'] <= booking.date_to) and (data['dateTo'] >= booking.date_from):
            return jsonify({'message': 'Booking already exists on selected dates'}), 400

    try:
        new_booking = Booking(
            listing_id=data['listing_id'],
            issuer_guest_id=int(current_user_id),
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

        while bookStartDate <= bookEndDate:  # Include end date
            Dates.append(bookStartDate)
            bookStartDate += timedelta(days=1)

        print(Dates)

        # Insert dates into listingBookedDates table

        bookedDatesbyListing = []
        for date in Dates:
            bookedDatesbyListing.append(ListingBookedDates(
                listing_id=data['listing_id'],
                booked_date=date

            ))
        db.session.add_all(bookedDatesbyListing)

        db.session.commit()
        return jsonify(
            {'message': 'Booking inserted successfully'}
                       ), 201


    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'message': 'Failed to insert booking. Please ensure the listing exists.',
            'error': str(e.orig)
        }), 400

    except Exception as e:
        db.session.rollback()  # Rollback for any other exceptions
        return jsonify({'message': 'An unexpected error occurred.', 'error': str(e)}), 500


@booking_bp.route('/get_bookings', methods=['GET'])
@jwt_required()
def get_bookings():
    """
    Fetch all bookings for the currently logged-in user.
    """
    current_user_id = get_jwt_identity()

    # Query bookings for the current user
    bookings = Booking.query.filter_by(issuer_guest_id=current_user_id).all()

    # Convert bookings to a list of dictionaries
    booking_list = [
        {
            "stay_id": booking.id,
            "listing_id": booking.listing_id,
            "date_from": booking.date_from,
            "date_to": booking.date_to,
            "names_of_people": booking.names_of_people,
            "amountOfPeople": booking.amountOfPeople
        }
        for booking in bookings
    ]

    return jsonify({"bookings": booking_list}), 200
