from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

# added to frontend
@auth_bp.route('/users', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    if not all([name, email, password, role]):
        return jsonify({'message': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': f'User already exists on {email}'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully'
    }), 201

# added to frontend

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Missing required fields'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User does not exist'}), 400

    if not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid password'}), 400

    from datetime import timedelta
    access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=24))
    return jsonify({
        'message': 'User logged in successfully',
        'access_token': access_token,
        'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}
    }), 200
