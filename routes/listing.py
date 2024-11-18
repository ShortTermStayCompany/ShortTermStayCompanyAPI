from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from Decorators.decorators import require_role
from models import db, Listing

listing_bp = Blueprint('listing', __name__)

@listing_bp.route('/insert_listing', methods=['POST'])
@jwt_required()
@require_role('host')

def insert_listing():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    required_fields = ['numberOfPeople', 'country', 'city', 'price']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    listing = Listing(
        user_id=int(current_user_id),
        title=data.get('title', '.'),
        numberOfPeople=data.get('numberOfPeople', 1),
        country=data['country'],
        city=data['city'],
        price=data['price']
    )
    db.session.add(listing)
    db.session.commit()
    return jsonify({'message': 'Listing inserted successfully'}), 201

@listing_bp.route('/listings', methods=['GET'])
@jwt_required(optional=True)

def get_listing():
    """
      Retrieve a paginated list of listings.

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

    listings = [listing.to_dict() for listing in paginated_listings.items]

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

    return jsonify({'data': listings, 'meta': meta}), 200

