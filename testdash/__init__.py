import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  # Initialize Flask
app.config.from_json('config.json')  # Import configuration from config.json
app.config.from_mapping(root_path=os.path.dirname(__file__))  # Setup root directory

db = SQLAlchemy(app)  # Initialize Database
db.create_all()  # Load DataBase
login_manager = LoginManager(app)  # Login manager (authentication)
login_manager.login_view = 'signin'  # Page for non-auth users
login_manager.login_message = 'Войдите, чтобы получить доступ к этой странице'  # Non-auth flash
login_manager.login_message_category = 'danger'  # Non-auth flash category

from . import routes  # Load routes
