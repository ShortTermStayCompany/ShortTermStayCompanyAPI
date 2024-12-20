import os
from flask import Flask, send_from_directory, render_template
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from models import db  # Importing the database object from models package
from routes import init_app  # Importing the function to register blueprints
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()


def create_app():
    app = Flask(__name__)

    ### Swagger UI Configuration ###
    SWAGGER_URL = '/swagger'  # URL to access Swagger UI
    API_URL = '/static/swagger.yaml'  # Path to swagger

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,  # Swagger UI endpoint
        API_URL,  # Swagger spec URL
        config={  # Swagger UI config overrides
            'app_name': "ShortTermStayCompanyAPI"
        }
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    ### Serve Swagger YAML ###
    @app.route('/static/<path:path>')
    def send_static(path):
        return send_from_directory('static', path)

    ### Home Route ###
    @app.route('/')
    def index():
        return render_template('index.html')

    ### Ping Route ###
    @app.route('/ping', methods=['GET'])
    def ping():
        return "Pong", 200

    ### Configure the database connection string ###
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USERNAME')
    SQL_password = os.getenv('DB_PASSWORD')
    driver = os.getenv('DB_DRIVER')

    # Check if all required environment variables are present
    if not all([server, database, username, SQL_password, driver]):
        raise SystemExit("Error: Missing required database environment variables")

    app.config[
        'SQLALCHEMY_DATABASE_URI'] = f'mssql+pyodbc://{username}:{SQL_password}@{server}/{database}?driver={driver}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configure JWT
    jwt_secret_key = os.getenv('JWT_SECRET_KEY')
    if not jwt_secret_key:
        raise SystemExit("Error: Missing JWT secret key")

    app.config['JWT_SECRET_KEY'] = jwt_secret_key
    jwt = JWTManager(app)

    # Initialize extensions
    db.init_app(app)  # Initialize the database
    CORS(app)  # Enable CORS

    # Register routes
    init_app(app)  # Register the blueprints using the init_app function

    with app.app_context():
        db.create_all()  # This will create all tables for the registered models

    return app


app = create_app()  # Create the app at the module level

if __name__ == '__main__':
    # app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=False)
