
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os

# Load environment variables from .env file (for local development)
load_dotenv()

app = Flask(__name__)

server = os.getenv('DB_SERVER', 'default_server')
database = os.getenv('DB_NAME', 'default_database')
username = os.getenv('DB_USERNAME', 'default_username')
SQL_password = os.getenv('DB_PASSWORD', 'default_password')
driver = os.getenv('DB_DRIVER', 'ODBC+Driver+18+for+SQL+Server')

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

    hashed_password = generate_password_hash(password, method='sha256')

    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        role=role
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),debug=True)
