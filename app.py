
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, CheckConstraint, and_
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from flask_jwt_extended import create_access_token, JWTManager
from datetime import timedelta, date, datetime

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

    id = db.Column(Integer,primary_key=True,autoincrement=True)
    name = db.Column(String(80),nullable=False)
    email = db.Column(String(250),unique=True,nullable=False)
    password = db.Column(String(1280),nullable=False)
    role = db.Column(String(5),CheckConstraint("role IN ('guest', 'host', 'admin')", name='role_check'),
        nullable=False,default='guest')

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(Integer,primary_key=True,autoincrement=True)
    user_id = db.Column(Integer,ForeignKey('users.id'),)
    title = db.Column(String(80),nullable=True)
    numberOfPeople = db.Column(Integer,CheckConstraint('NumberOfPeople >= 1 AND NumberOfPeople <= 32', name='number_of_people_check'),
    nullable=False,default=1)
    country = db.Column(String(128),nullable=False)
    city = db.Column(String(128),nullable=False)
    price = db.Column(Float,nullable=False,)
####
class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    listing_id = db.Column(db.Integer,db.ForeignKey('listings.id'),nullable=False)
    issuer_guest_id = db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    date_from = db.Column(db.Date,nullable=False)
    date_to = db.Column(db.Date,nullable=False)
    names_of_people = db.Column(db.String(250),nullable=False)
    amountOfPeople = db.Column(db.Integer, nullable=True)

class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    stay_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500))
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_between_1_and_5'),)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')  # host / guest / admin

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


@app.route('/insert_listing', methods=['POST'])
def insert_listing():
    data = request.get_json()

    if 'user_id' not in data:
        return jsonify({'message': 'User ID is required'}), 400

    # Query user by id instead of userToken
    user = User.query.filter_by(id=data['user_id']).first()
    if not user:
        return jsonify({'message': 'Invalid user ID'}), 403
    if user.role.lower() != 'host':
        return jsonify({'message': 'Only hosts are allowed to insert listings'}), 403

    required_fields = ['numberOfPeople', 'country', 'city', 'price']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    listing = Listing(
        user_id=user.id,
        title=data.get('title', '.'),
        numberOfPeople=data.get('numberOfPeople', 1),
        country=data.get('country'),
        city=data.get('city'),
        price=data.get('price')
    )

    db.session.add(listing)
    db.session.commit()
    return jsonify({'message': 'Listing inserted successfully'}), 201

@app.route('/insert_booking', methods=['POST'])
def insert_booking():
    data = request.get_json()
    if 'user_id' not in data:
        # return jsonify({'message': 'User ID is required / Need to login first'}), 400
        return jsonify({'message': 'Missing required fields'}), 400

    if 'listing_id' not in data:
        return jsonify({'message': 'Missing required fields'}), 400

        # return jsonify({'message': 'Listing ID is required'}), 400
    required_fields = ['user_id', 'title', 'dateFrom', 'dateTo', 'namesOfPeople']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    results = db.session.query(Booking).filter(
        Booking.listing_id == data['listing_id']
    ).all()
    print(f"Results from database query: {results}")


    for result in results:
        data['dateFrom'] = datetime.strptime(data['dateFrom'], '%Y-%m-%d').date()
        data['dateTo'] = datetime.strptime(data['dateTo'], '%Y-%m-%d').date()
        book_start_date = result.date_from
        book_end_date = result.date_to
        if (data['dateFrom'] <= book_end_date) and (data['dateTo'] >= book_start_date):
            return jsonify({'message': 'Booking already exists on selected dates'}), 400
    else:
        booking = Booking(
            listing_id=data['listing_id'],
            issuer_guest_id=data['user_id'],
            date_from=data['dateFrom'],
            date_to=data['dateTo'],
            names_of_people=data['namesOfPeople'],
            amountOfPeople=data.get('amountOfPeople', 1)

        )

        db.session.add(booking)
        db.session.commit()
        return jsonify({'message': 'Booking inserted successfully'}), 201

@app.route('/insert_review', methods=['POST'])
def insert_review():
    data = request.get_json()
    if 'user_id' not in data:
        # return jsonify({'message': 'User ID is required / Need to login first'}), 400
        return jsonify({'message': 'Missing required fields'}), 400

    if 'stay_id' not in data:
        # return jsonify({'message': 'Stay ID is required'}), 400
        return jsonify({'message': 'Missing required fields'}), 400

    required_fields = ['rating', 'comment']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    results = db.session.query(Booking).filter(
        and_(
            Booking.issuer_guest_id == data['user_id'],
            Booking.id == data['stay_id']
        )
    ).first()

    if not results:
        return jsonify({'message': 'Booking does not exist'}), 400

    review = Review(
        guest_id=data['user_id'],
        stay_id=data['stay_id'],
        rating=data.get('rating', 1),
        comment=data.get('comment', ''),
    )
    db.session.add(review)
    db.session.commit()
    return jsonify({'message': 'Review inserted successfully'}), 201

@app.route('/report_listings', methods=['GET'])
def report_listing():
    data = request.get_json()


def drop_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

if __name__ == '__main__':
    # drop_database()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),debug=True)


'''
test/register

{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "password123",
  "role": "host"
}





'''