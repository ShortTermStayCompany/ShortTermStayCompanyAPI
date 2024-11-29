from .auth import auth_bp
from .listing import listing_bp
from .booking import booking_bp
from .report import report_bp
from .review import review_bp

def init_app(app):
    # Version 1 Blueprints
    app.register_blueprint(auth_bp, url_prefix='/v1/auth')
    app.register_blueprint(listing_bp, url_prefix='/v1/listing')
    app.register_blueprint(booking_bp, url_prefix='/v1/booking')
    app.register_blueprint(review_bp, url_prefix='/v1/review')
    app.register_blueprint(report_bp, url_prefix='/v1/report')
