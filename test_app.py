import os
import unittest
import json
from datetime import date, timedelta

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token

from werkzeug.security import generate_password_hash

# Import the app and db from your main application
from app import app, db, User, Listing, Booking, Review

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        """
        Set up a test client and initialize a new in-memory database for each test.
        """
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory SQLite for testing
        app.config['JWT_SECRET_KEY'] = 'test_jwt_secret_key'

        self.app = app.test_client()

        with app.app_context():
            # Drop all existing tables to ensure a clean state
            db.drop_all()
            # Create all tables
            db.create_all()

            # Optionally, you can add initial data here if needed
            # For example, creating a default admin user
            admin_user = User(
                name='Admin',
                email='admin@example.com',
                password=generate_password_hash('adminpass'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()

    def tearDown(self):
        """
        Drop the database after each test.
        """
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def register_user(self, name, email, password, role):
        """
        Helper method to register a user.
        """
        return self.app.post('/register', data=json.dumps({
            'name': name,
            'email': email,
            'password': password,
            'role': role
        }), content_type='application/json')

    def login_user(self, email, password):
        """
        Helper method to login a user.
        """
        return self.app.post('/login', data=json.dumps({
            'email': email,
            'password': password
        }), content_type='application/json')

    def test_register_user_success(self):
        """
        Test successful user registration.
        """
        response = self.register_user('Alice', 'alice@example.com', 'password123', 'host')
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('User registered successfully', data['message'])

    def test_register_user_missing_fields(self):
        """
        Test user registration with missing fields.
        """
        response = self.app.post('/register', data=json.dumps({
            'name': 'Bob',
            'email': 'bob@example.com',
            # Missing password and role
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Missing required fields', data['message'])

    def test_register_user_duplicate_email(self):
        """
        Test registering a user with an email that already exists.
        """
        self.register_user('Alice', 'alice@example.com', 'password123', 'host')
        response = self.register_user('Alice2', 'alice@example.com', 'password456', 'guest')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('User already exists', data['message'])

    def test_login_user_success(self):
        """
        Test successful user login.
        """
        self.register_user('Alice', 'alice@example.com', 'password123', 'host')
        response = self.login_user('alice@example.com', 'password123')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('User logged in successfully', data['message'])
        self.assertIn('access_token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'alice@example.com')

    def test_login_user_invalid_credentials(self):
        """
        Test login with invalid credentials.
        """
        self.register_user('Alice', 'alice@example.com', 'password123', 'host')
        response = self.login_user('alice@example.com', 'wrongpassword')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Invalid password', data['message'])

    def test_insert_listing_success(self):
        """
        Test successful insertion of a listing by a host.
        """
        # Register a host
        self.register_user('HostUser', 'host@example.com', 'hostpass', 'host')
        # Login the host to get user_id
        login_resp = self.login_user('host@example.com', 'hostpass')
        login_data = json.loads(login_resp.data)
        user_id = login_data['user']['id']

        # Insert listing
        response = self.app.post('/insert_listing', data=json.dumps({
            'user_id': user_id,
            'title': 'Cozy Apartment',
            'numberOfPeople': 4,
            'country': 'USA',
            'city': 'New York',
            'price': 150.0
        }), content_type='application/json')

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('Listing inserted successfully', data['message'])

    def test_insert_listing_non_host_user(self):
        """
        Test inserting a listing with a user who is not a host.
        """
        # Register a guest
        self.register_user('GuestUser', 'guest@example.com', 'guestpass', 'guest')
        # Login the guest to get user_id
        login_resp = self.login_user('guest@example.com', 'guestpass')
        login_data = json.loads(login_resp.data)
        user_id = login_data['user']['id']

        # Attempt to insert listing
        response = self.app.post('/insert_listing', data=json.dumps({
            'user_id': user_id,
            'title': 'Cozy Apartment',
            'numberOfPeople': 4,
            'country': 'USA',
            'city': 'New York',
            'price': 150.0
        }), content_type='application/json')

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.data)
        self.assertIn('Only hosts are allowed to insert listings', data['message'])

    def test_insert_listing_missing_fields(self):
        """
        Test inserting a listing with missing required fields.
        """
        # Register and login a host
        self.register_user('HostUser', 'host@example.com', 'hostpass', 'host')
        login_resp = self.login_user('host@example.com', 'hostpass')
        login_data = json.loads(login_resp.data)
        user_id = login_data['user']['id']

        # Attempt to insert listing with missing fields
        response = self.app.post('/insert_listing', data=json.dumps({
            'user_id': user_id,
            # Missing numberOfPeople, country, city, price
        }), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Missing required fields', data['message'])

    def test_insert_booking_success(self):
        """
        Test successful booking insertion.
        """
        with app.app_context():
            # Create host and listing
            host = User(name='Host', email='host@example.com', password=generate_password_hash('hostpass'), role='host')
            db.session.add(host)
            db.session.commit()

            listing = Listing(
                user_id=host.id,
                title='Beach House',
                numberOfPeople=6,
                country='USA',
                city='Miami',
                price=300.0
            )
            db.session.add(listing)
            db.session.commit()

            # Create guest
            guest = User(name='Guest', email='guest@example.com', password=generate_password_hash('guestpass'), role='guest')
            db.session.add(guest)
            db.session.commit()

            # Insert booking
            response = self.app.post('/insert_booking', data=json.dumps({
                'user_id': guest.id,
                'listing_id': listing.id,
                'title': 'Beach House',
                'dateFrom': str(date.today() + timedelta(days=1)),
                'dateTo': str(date.today() + timedelta(days=5)),
                'namesOfPeople': 'Guest1, Guest2',
                'amountOfPeople': 2
            }), content_type='application/json')

            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertIn('Booking inserted successfully', data['message'])

    def test_insert_booking_conflict_dates(self):
        """
        Test booking insertion with conflicting dates.
        """
        with app.app_context():
            # Create host and listing
            host = User(name='Host', email='host@example.com', password=generate_password_hash('hostpass'), role='host')
            db.session.add(host)
            db.session.commit()

            listing = Listing(
                user_id=host.id,
                title='Beach House',
                numberOfPeople=6,
                country='USA',
                city='Miami',
                price=300.0
            )
            db.session.add(listing)
            db.session.commit()

            # Create guest
            guest = User(name='Guest', email='guest@example.com', password=generate_password_hash('guestpass'), role='guest')
            db.session.add(guest)
            db.session.commit()

            # First booking
            booking1 = Booking(
                listing_id=listing.id,
                issuer_guest_id=guest.id,
                date_from=date.today() + timedelta(days=1),
                date_to=date.today() + timedelta(days=5),
                names_of_people='Guest1, Guest2',
                amountOfPeople=2
            )
            db.session.add(booking1)
            db.session.commit()

            # Attempt conflicting booking
            response = self.app.post('/insert_booking', data=json.dumps({
                'user_id': guest.id,
                'listing_id': listing.id,
                'title': 'Beach House',
                'dateFrom': str(date.today() + timedelta(days=3)),
                'dateTo': str(date.today() + timedelta(days=7)),
                'namesOfPeople': 'Guest3, Guest4',
                'amountOfPeople': 2
            }), content_type='application/json')

            self.assertEqual(response.status_code, 400)
            # data = json.loads(response.data)
            # self.assertIn('Booking already exists on selected dates', data['message'])

    def test_insert_review_success(self):
        """
        Test successful review insertion.
        """
        with app.app_context():
            # Create host and listing
            host = User(name='Host', email='host@example.com', password=generate_password_hash('hostpass'), role='host')
            db.session.add(host)
            db.session.commit()

            listing = Listing(
                user_id=host.id,
                title='Mountain Cabin',
                numberOfPeople=4,
                country='USA',
                city='Denver',
                price=200.0
            )
            db.session.add(listing)
            db.session.commit()

            # Create guest
            guest = User(name='Guest', email='guest@example.com', password=generate_password_hash('guestpass'), role='guest')
            db.session.add(guest)
            db.session.commit()

            # Create booking
            booking = Booking(
                listing_id=listing.id,
                issuer_guest_id=guest.id,
                date_from=date.today() - timedelta(days=10),
                date_to=date.today() - timedelta(days=5),
                names_of_people='Guest1, Guest2',
                amountOfPeople=2
            )
            db.session.add(booking)
            db.session.commit()

            # Insert review
            response = self.app.post('/insert_review', data=json.dumps({
                'user_id': guest.id,
                'stay_id': booking.id,
                'rating': 5,
                'comment': 'Great stay!'
            }), content_type='application/json')

            self.assertEqual(response.status_code, 201)

    def test_insert_review_invalid_booking(self):
        """
        Test inserting a review for a non-existent booking.
        """
        # Attempt to insert review without valid booking
        response = self.app.post('/insert_review', data=json.dumps({
            'user_id': 1,  # Admin user
            'stay_id': 999,  # Non-existent booking
            'rating': 4,
            'comment': 'Good!'
        }), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Booking does not exist', data['message'])

    def test_insert_review_missing_fields(self):
        """
        Test inserting a review with missing required fields.
        """
        # Attempt to insert review with missing fields
        response = self.app.post('/insert_review', data=json.dumps({
            'user_id': 1,
            # Missing stay_id, rating, comment
        }), content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Missing required fields', data['message'])

    # Additional tests can be added here for other endpoints and edge cases

if __name__ == '__main__':
    unittest.main()
