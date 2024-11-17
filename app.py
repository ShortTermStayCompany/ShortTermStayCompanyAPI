
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from flask_jwt_extended import create_access_token, JWTManager

# Load environment variables from .env file (for local development)
load_dotenv()


app = Flask(__name__)

# Fetch environment variables for the database
server = os.getenv('DB_SERVER')
database = os.getenv('DB_NAME')
username = os.getenv('DB_USERNAME')
SQL_password = os.getenv('DB_PASSWORD')
driver = os.getenv('DB_DRIVER')

# Fetch the JWT secret key from an environment variable
jwt_secret_key = os.getenv('JWT_SECRET_KEY')

# Check if any of the required environment variables are missing
missing_vars = [var for var, value in {
    'DB_SERVER': server,
    'DB_NAME': database,
    'DB_USERNAME': username,
    'DB_PASSWORD': SQL_password,
    'DB_DRIVER': driver,
    'JWT_SECRET_KEY': jwt_secret_key
}.items() if not value]

if missing_vars:
    raise SystemExit(f"Error: Missing required environment variables: {', '.join(missing_vars)}")

# Configure the JWT secret key
app.config['JWT_SECRET_KEY'] = jwt_secret_key

# Initialize JWTManager
jwt = JWTManager(app)

connection_string = f'mssql+pyodbc://{username}:{SQL_password}@{server}/{database}?driver={driver}'

app.config['SQLALCHEMY_DATABASE_URI'] = connection_string

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name = db.Column(
        String(80),
        nullable=False
    )
    email = db.Column(
        String(250),
        unique=True,
        nullable=False
    )
    password = db.Column(
        String(128),
        nullable=False
    )
    role = db.Column(
        String(5),
        CheckConstraint("role IN ('guest', 'host', 'admin')", name='role_check'),
        nullable=False,
        default='guest'
    )

class Listing(db.Model):
    __tablename__ = 'listings'

    id = db.Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name = db.Column(
        String(80),
        nullable=False
    )
    NumberOfPeople = db.Column(
        Integer,
        CheckConstraint('NumberOfPeople >= 1 AND NumberOfPeople <= 32', name='number_of_people_check'),
        nullable=False,
        default=1
    )
    Country = db.Column(
        String(128),
        nullable=False
    )
    City = db.Column(
        String(128),
        nullable=False
    )
    Price = db.Column(
        Float,
        nullable=False,
    )
####
class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer,
                   primary_key=True,
                   autoincrement=True)
    listing_id = db.Column(db.Integer,
                           db.ForeignKey('listings.id'),
                           nullable=False)
    guest_id = db.Column(db.Integer,
                         db.ForeignKey('users.id'),
                         nullable=False)
    date_from = db.Column(db.Date,
                          nullable=False)
    date_to = db.Column(db.Date,
                        nullable=False)
    names_of_people = db.Column(db.String(250),
                                nullable=False)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stay_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500))
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_between_1_and_5'),
    )




@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')  # host / guest

    if not all([name, email, password, role]):
        return jsonify({'message': 'Missing required fields'}), 400

    # Check if user already exists
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

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not all([email, password]):
        return jsonify({'message': 'Missing required fields'}), 400
    # check if user exisrt
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'User does not exist'}), 400
    # validate user information
    if not check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid password'}), 400

    # Create an access token
    access_token = create_access_token(identity=user.id)

    return jsonify({
        'message': 'User logged in successfully',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
    }), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),debug=True)
