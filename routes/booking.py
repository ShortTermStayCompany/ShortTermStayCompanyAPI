from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from Decorators.decorators import require_role
from models import db, Booking, ListingBookedDates, Listing
from datetime import datetime, timedelta

booking_bp = Blueprint('booking', __name__)

@booking_bp.route('/insert_booking', methods=['POST'])
@jwt_required()
@require_role('guest')

def insert_booking():
    print("insert_booking API called")  

    current_user_id = get_jwt_identity()
    print(f"Current User ID: {current_user_id}")

    data = request.get_json()
    print(f"Request Data: {data}")

    required_fields = ['listing_id', 'dateFrom', 'dateTo', 'namesOfPeople']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        print(f"Missing fields: {missing_fields}")
        return jsonify({'message': f'Missing required fields: {",".join(missing_fields)}'}), 400

    try:
        data['dateFrom'] = datetime.strptime(data['dateFrom'], '%Y-%m-%d').date()
        data['dateTo'] = datetime.strptime(data['dateTo'], '%Y-%m-%d').date()
        print(f"Parsed Dates - From: {data['dateFrom']}, To: {data['dateTo']}")
    except ValueError:
        print("Invalid date format in request")
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    listing = db.session.query(Listing).filter_by(id=data['listing_id']).first()
    print(f"Listing Found: {listing}")

    if not listing:
        print("Listing does not exist")
        return jsonify({'message': 'Listing does not exist.'}), 400

    if not (listing.availableFrom <= data['dateFrom'] <= listing.availableTo) or not (listing.availableFrom <= data['dateTo'] <= listing.availableTo):
        print(f"Booking dates out of range. Listing Available Range: {listing.availableFrom} to {listing.availableTo}")
        return jsonify({
            'message': 'Booking dates must be within the listing\'s availability range.',
            'available_range': {
                'from': listing.availableFrom.strftime('%Y-%m-%d'),
                'to': listing.availableTo.strftime('%Y-%m-%d')
            }
        }), 400

    unavailable_dates = db.session.query(ListingBookedDates.booked_date).filter(
        ListingBookedDates.listing_id == data['listing_id'],
        ListingBookedDates.booked_date.between(data['dateFrom'], data['dateTo'])
    ).all()
    print(f"Unavailable Dates Found: {unavailable_dates}")

    if unavailable_dates:
        unavailable_dates_str = [date[0].strftime('%Y-%m-%d') for date in unavailable_dates]
        print(f"Conflicting Unavailable Dates: {unavailable_dates_str}")
        return jsonify({
            'message': 'Selected dates are not available for booking.',
            'unavailable_dates': unavailable_dates_str
        }), 400

    existing_bookings = db.session.query(Booking).filter(
        Booking.listing_id == data['listing_id']
    ).all()
    print(f"Existing Bookings Found: {existing_bookings}")
    for booking in existing_bookings:
        if (data['dateFrom'] <= booking.date_to) and (data['dateTo'] >= booking.date_from):
            print(f"Overlapping Booking Found: {booking}")
            return jsonify({'message': 'Booking already exists on selected dates'}), 400

    try:
        # Create a new booking
        new_booking = Booking(
            listing_id=data['listing_id'],
            issuer_guest_id=int(current_user_id),
            date_from=data['dateFrom'],
            date_to=data['dateTo'],
            names_of_people=data['namesOfPeople'],
            amountOfPeople=data.get('amountOfPeople', 1)  # Default to 1 if not provided
        )
        db.session.add(new_booking)
        print(f"New Booking Added: {new_booking}")  # Log new booking

        # Generate all dates between bookStartDate and bookEndDate
        bookStartDate = data['dateFrom']
        bookEndDate = data['dateTo']
        Dates = []
        while bookStartDate <= bookEndDate:  # Include the end date
            Dates.append(bookStartDate)
            bookStartDate += timedelta(days=1)

        print(f"Generated Booking Dates: {Dates}")  # Log generated dates

        # Insert dates into the listingBookedDates table
        bookedDatesbyListing = [
            ListingBookedDates(
                listing_id=data['listing_id'],
                booked_date=date
            )
            for date in Dates
        ]
        db.session.add_all(bookedDatesbyListing)
        print(f"Booked Dates Added: {bookedDatesbyListing}")  # Log booked dates

        # Commit the transaction to the database
        db.session.commit()
        print("Transaction committed successfully")  # Log successful transaction

        # Return a success message
        return jsonify({'message': 'Booking inserted successfully'}), 201

    except IntegrityError as e:
        # Handle database integrity errors (e.g., missing foreign key constraints)
        db.session.rollback()
        print(f"Integrity Error: {str(e.orig)}")  # Log integrity error
        return jsonify({
            'message': 'Failed to insert booking. Please ensure the listing exists.',
            'error': str(e.orig)
        }), 400

    except Exception as e:
        # Handle any other unexpected exceptions
        db.session.rollback()
        print(f"Unexpected Error: {str(e)}")  # Log unexpected error
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
