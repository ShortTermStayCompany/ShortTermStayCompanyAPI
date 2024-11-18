from flask import jsonify, request, Blueprint
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from Decorators.decorators import require_role
from models import db, Listing, Review, Booking

report_bp = Blueprint('report', __name__)


@report_bp.route('/report_listings', methods=['GET'])
@jwt_required()
@require_role('admin')
def report_listings():

    min_rating = request.args.get('min_rating', type=float)
    max_rating = request.args.get('max_rating', type=float)

    query = (
        db.session.query(
            Listing.id,
            Listing.title,
            Listing.country,
            Listing.city,
            Listing.price,
            func.avg(Review.rating).label('average_rating'),
            func.count(Review.id).label('review_count')
        )
        .outerjoin(Booking, Booking.listing_id == Listing.id)  # Join Booking with Listing
        .outerjoin(Review, Review.stay_id == Booking.id)  # Join Review with Booking
        .group_by(
            Listing.id,
            Listing.title,
            Listing.country,
            Listing.city,
            Listing.price
        )  # Group by all selected columns from Listing
    )

    if min_rating is not None:
        query = query.having(func.avg(Review.rating) >= min_rating)
    if max_rating is not None:
        query = query.having(func.avg(Review.rating) <= max_rating)

    results = query.all()

    data = [
        {
            'id': listing.id,
            'title': listing.title,
            'country': listing.country,
            'city': listing.city,
            'price': listing.price,
            'average_rating': listing.average_rating if listing.average_rating is not None else "No reviews",
            'review_count': listing.review_count
        }
        for listing in results
    ]

    return jsonify({
        'message': 'Report generated successfully',
        'data': data
    }), 200
