from datetime import timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from jinja2.utils import missing
from sqlalchemy import func

from Decorators.decorators import require_role
from models import db, Listing, ListingBookedDates, Review

listing_bp = Blueprint('listing', __name__)

@listing_bp.route('/insert_listing', methods=['POST'])
@jwt_required()
@require_role('host')

def insert_listing():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ['numberOfPeople', 'country', 'city', 'price','availableFrom','availableTo']
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    if missing_fields:
        return jsonify({'message': f'Missing required fields: {",".join(missing_fields)}'}), 400

    # Check if a listing with the same attributes already exists
    existing_listing = Listing.query.filter_by(
        user_id=current_user_id,
        title=data.get('title', '.'),
        numberOfPeople=data.get('numberOfPeople', 1),
        country=data['country'],
        city=data['city'],
        price=data['price'],
        availableFrom=data['availableFrom'],
        availableTo=data['availableTo']
    ).first()

    if existing_listing:
        return jsonify({'message': 'Listing already exists'}), 400

    listing = Listing(
        user_id=int(current_user_id),
        title=data.get('title', '.'),
        numberOfPeople=data.get('numberOfPeople', 1),
        country=data['country'],
        city=data['city'],
        price=data['price'],
        availableFrom=data['availableFrom'],
        availableTo=data['availableTo'],
    )
    db.session.add(listing)
    db.session.commit()
    return jsonify({'message': 'Listing inserted successfully'}), 201

@listing_bp.route('/listings', methods=['GET'])
@jwt_required(optional=True)
def get_listing():
    """
    Retrieve a paginated list of listings, including unavailable dates and average ratings.

    Query Parameters:
        - page (int): Page number (default: 1)
        - per_page (int): Listings per page (default: 10, max: 100)

    Returns:
        JSON response containing listings data and pagination metadata.
    """
    DEFAULT_PAGE = 1
    DEFAULT_PER_PAGE = 10
    MAX_PER_PAGE = 100
    page = request.args.get('page', default=DEFAULT_PAGE, type=int)
    per_page = request.args.get('per_page', default=DEFAULT_PER_PAGE, type=int)
    if page < 1:
        return jsonify({'message': 'Page number must be 1 or greater.'}), 400
    if per_page < 1 or per_page > MAX_PER_PAGE:
        return jsonify({'message': f'per_page must be between 1 and {MAX_PER_PAGE}.'}), 400

    query = Listing.query.order_by(Listing.id.desc())
    paginated_listings = query.paginate(page=page, per_page=per_page, error_out=False)

    listings_with_extra_data = []

    for listing in paginated_listings.items:
        # Fetch booked dates for the listing
        booked_dates = db.session.query(ListingBookedDates.booked_date).filter(
            ListingBookedDates.listing_id == listing.id
        ).all()
        booked_dates_set = set(date[0] for date in booked_dates)

        # If all dates in the range are booked, skip this listing
        if len(booked_dates_set) == (listing.availableTo - listing.availableFrom).days + 1:
            continue

        # Sort unavailable dates for readability
        unavailable_dates = list(booked_dates_set)
        unavailable_dates.sort()

        # Calculate the average rating for the listing
        average_rating = db.session.query(func.avg(Review.rating)).filter(
            Review.stay_id == listing.id
        ).scalar()

        # Ensure average_rating is a float or 0 if no reviews
        average_rating = round(average_rating, 2) if average_rating else 0.0

        # Append listing with unavailable dates and average rating
        listings_with_extra_data.append({
            **listing.to_dict(),
            'unavailableDates': unavailable_dates,
            'averageRating': average_rating
        })

    meta = {
        'page': paginated_listings.page,
        'per_page': paginated_listings.per_page,
        'total_pages': paginated_listings.pages,
        'total_items': paginated_listings.total,
        'has_next': paginated_listings.has_next,
        'has_prev': paginated_listings.has_prev,
        'next_page': paginated_listings.next_num if paginated_listings.has_next else None,
        'prev_page': paginated_listings.prev_num if paginated_listings.has_prev else None
    }

    return jsonify({'data': listings_with_extra_data, 'meta': meta}), 200