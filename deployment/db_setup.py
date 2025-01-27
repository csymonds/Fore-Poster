from werkzeug.security import generate_password_hash
from fore_poster import app, db, User
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

with app.app_context():
    db.drop_all()  # Reset database
    db.create_all()
    
    # Create admin user
    default_user = User(
        username=os.getenv('ADMIN_USERNAME'),
        password=generate_password_hash(os.getenv('ADMIN_PASSWORD'))
    )
    db.session.add(default_user)
    db.session.commit()