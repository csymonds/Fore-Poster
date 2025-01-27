from werkzeug.security import generate_password_hash
from env_handler import load_environment

# Load environment variables before importing the app
load_environment()

# Now import the app and models
from fore_poster import app, db, User

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

    print("Database setup complete.")
    print(f"Created admin user: {os.getenv('ADMIN_USERNAME')}")