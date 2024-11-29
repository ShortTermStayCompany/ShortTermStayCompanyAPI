from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from Decorators.decorators import require_role
from models import db, Booking, Review
from sqlalchemy import and_

review_bp = Blueprint('review', __name__)

@review_bp.route('/insert_review', methods=['POST'])
@jwt_required()
@require_role('guest')
def insert_review():
    current_user_id = get_jwt_identity()

    data = request.get_json()

    # Validate presence of 'stay_id'
    if 'stay_id' not in data:
        return jsonify({
            'message': 'Missing required fields',
            'error': "The 'stay_id' field is required."
        }), 400

    # Validate required fields
    required_fields = ['rating', 'comment']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({
            'message': 'Missing required fields',
            'error': f"The {', '.join(missing_fields)} field(s) are required."
        }), 400

    stay_id = data['stay_id']

    # Corrected: Fetch booking based on Booking.id (stay_id) and current_user_id
    booking = db.session.query(Booking).filter(
        and_(
            Booking.id == stay_id,  # Corrected from Booking.listing_id to Booking.id
            Booking.issuer_guest_id == current_user_id
        )
    ).first()

    if not booking:
        return jsonify({
            'message': 'Booking does not exist',
            'error': f"No booking found with stay_id '{stay_id}'."
        }), 400

    # Check if a review already exists for this booking by the current user
    existing_review = db.session.query(Review).filter(
        and_(
            Review.stay_id == stay_id,
            Review.guest_id == current_user_id
        )
    ).first()

    if existing_review:
        return jsonify({
            'message': 'Review already exists',
            'error': 'You have already reviewed this booking.'
        }), 400

    # Validate rating value
    rating = data.get('rating')
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({
            'message': 'Invalid rating value',
            'error': 'Rating must be between 1 and 5.'
        }), 400

    # Create new review
    new_review = Review(
        guest_id=current_user_id,
        stay_id=stay_id,
        rating=rating,
        comment=data.get('comment', '')
    )
    db.session.add(new_review)
    db.session.commit()

    return jsonify({'message': 'Review inserted successfully'}), 201
