from .auth import auth_bp
from .listing import listing_bp
from .booking import booking_bp
from .report import report_listings
from .review import review_bp
from .report import report_bp

def init_app(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(listing_bp, url_prefix='/listing')
    app.register_blueprint(booking_bp, url_prefix='/booking')
    app.register_blueprint(review_bp, url_prefix='/review')
    app.register_blueprint(report_bp, url_prefix='/report')
