from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from models import db, Booking, Review
from sqlalchemy import and_

review_bp = Blueprint('review', __name__)

@review_bp.route('/insert_review', methods=['POST'])
@jwt_required()

def insert_review():
    data = request.get_json()
    if 'user_id' not in data:
        return jsonify({'message': 'User ID is required'}), 400
    if 'stay_id' not in data:
        return jsonify({'message': 'Stay ID is required'}), 400

    required_fields = ['rating', 'comment']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    booking = db.session.query(Booking).filter(
        and_(
            Booking.issuer_guest_id == data['user_id'],
            Booking.id == data['stay_id']
        )
    ).first()

    if not booking:
        return jsonify({'message': 'Booking does not exist'}), 400

    new_review = Review(
        guest_id=data['user_id'],
        stay_id=data['stay_id'],
        rating=data.get('rating', 1),
        comment=data.get('comment', '')
    )
    db.session.add(new_review)
    db.session.commit()
    return jsonify({'message': 'Review inserted successfully'}), 201
