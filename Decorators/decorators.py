# decorators.py

import functools
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User


def require_role(*roles):
    def decorator(fn):
        @functools.wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.filter_by(id=int(current_user_id)).first()

            if not user:
                return jsonify({'message': 'User not found'}), 404

            user_role = user.role.lower()
            allowed_roles = [role.lower() for role in roles]

            if user_role not in allowed_roles:
                return jsonify({'message': 'Access forbidden: insufficient permissions'}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
