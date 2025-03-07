from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import jwt
import os
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.security import generate_password_hash, check_password_hash
import tweepy
from env_handler import load_environment, get_env_var
from functools import wraps
from config import Config
from datetime import datetime, timedelta
import pytz
import hashlib

CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:4173').split(',')

# Cross-platform password hashing utilities
def robust_password_hash(password):
    """
    Create a password hash that works across environments.
    Falls back to different methods if preferred ones aren't available.
    """
    # Check if scrypt is available (default in newer Python versions)
    if hasattr(hashlib, 'scrypt'):
        try:
            return generate_password_hash(password)  # Default is scrypt
        except Exception:
            pass  # Fall through to alternatives
    
    # Use pbkdf2 which is widely available
    return generate_password_hash(password, method='pbkdf2:sha256')

def robust_password_verify(pwhash, password):
    """
    Verify a password against a hash in a way that works across environments.
    """
    try:
        logging.info(f"Verifying password against hash: {pwhash[:20]}...")
        result = check_password_hash(pwhash, password)
        logging.info(f"Standard verification result: {result}")
        return result
    except Exception as e:
        # If standard check fails (rare), log it with details
        logging.error(f"Password verification error: {str(e)}")
        logging.error(f"Hash format: {pwhash[:10]}...")
        return False

def get_eastern_tz():
    """Get US Eastern timezone."""
    return pytz.timezone('America/New_York')

def parse_iso_datetime(datetime_str: str) -> datetime:
    """
    Parse ISO format datetime string, handling UTC 'Z' timezone designator.
    Always converts to UTC for storage.
    """
    try:
        eastern_tz = get_eastern_tz()
        
        # Replace 'Z' with '+00:00' for UTC
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str.replace('Z', '+00:00')
            
        # Parse the datetime
        dt = datetime.fromisoformat(datetime_str)
        
        # If the datetime has no timezone, assume it's in Eastern time
        if dt.tzinfo is None:
            dt = eastern_tz.localize(dt)
            
        # Convert to UTC for storage
        return dt.astimezone(pytz.UTC)
    except ValueError as e:
        app.logger.error(f"Invalid datetime format: {datetime_str}")
        raise ValueError(f"Invalid datetime format: {str(e)}")

def format_datetime_for_response(dt: datetime) -> str:
    """
    Format datetime for API response.
    Converts from UTC (storage) to Eastern time and returns ISO format.
    """
    eastern_tz = get_eastern_tz()
    
    # Ensure datetime is timezone-aware UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    elif dt.tzinfo != pytz.UTC:
        dt = dt.astimezone(pytz.UTC)
        
    # Convert to Eastern time
    eastern_time = dt.astimezone(eastern_tz)
    return eastern_time.isoformat()

def is_scheduled_time_future(dt: datetime) -> bool:
    """
    Check if a datetime is in the future, handling timezone awareness properly.
    """
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt > datetime.now(pytz.UTC)


# Set up logging
def setup_logging(app):
    # Create logs directory if it doesn't exist
    log_dir = '/var/log/fore-poster'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set up file handler for all logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'fore_poster.log'),
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Set up error log handler
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=1024 * 1024,
        backupCount=10
    )
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    error_handler.setLevel(logging.ERROR)

    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    # Log startup message
    app.logger.info('Fore-Poster startup')

app = Flask(__name__)
setup_logging(app)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Load configuration
load_environment()
Config.init_app(os.getenv('APP_ENV', 'development'))
app.config.from_object(Config)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC))
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, posted, failed
    platform = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.String(120))  # Store platform post ID after posting

    @property
    def eastern_scheduled_time(self):
        """Get scheduled time in Eastern timezone."""
        if self.scheduled_time is None:
            return None
        return format_datetime_for_response(self.scheduled_time)
class XClient:
    def __init__(self):
        self.test_mode = app.config.get('TESTING', False)
        if not self.test_mode:
            self.client = tweepy.Client(
                consumer_key=get_env_var('X_API_KEY'),
                consumer_secret=get_env_var('X_API_SECRET'),
                access_token=get_env_var('X_ACCESS_TOKEN'),
                access_token_secret=get_env_var('X_ACCESS_TOKEN_SECRET')
            )
            app.logger.info('X client initialized')
    
    def post(self, content: str) -> dict:
        if self.test_mode:
            app.logger.info("Test mode: Skipping actual post")
            return {'success': True, 'post_id': 'test_123'}
            
        try:
            app.logger.info(f"Attempting to post to X: {content[:50]}...")
            response = self.client.create_tweet(text=content)
            app.logger.info(f"Successfully posted to X, post_id: {response.data['id']}")
            return {'success': True, 'post_id': response.data['id']}
        except Exception as e:
            app.logger.error(f"Error posting to X: {str(e)}")
            return {'success': False, 'error': str(e)}

@app.before_request
def log_request():
    app.logger.info(f"""
Request:
  Method: {request.method}
  URL: {request.url}
  Headers: {dict(request.headers)}
  Body: {request.get_data(as_text=True)}
    """)

@app.after_request
def log_response(response):
    app.logger.info(f"""
Response:
  Status: {response.status}
  Headers: {dict(response.headers)}
  Body: {response.get_data(as_text=True)}
    """)
    return response

@app.errorhandler(Exception)
def handle_error(error):
    app.logger.error(f"Unhandled error: {str(error)}", exc_info=True)
    return jsonify(error="Internal server error"), 500

class AuthHandler:
    def __init__(self):
        self.secret = get_env_var('JWT_SECRET')
        if not self.secret:
            raise EnvironmentError("JWT_SECRET environment variable is required")
            
    def generate_token(self, user_id: int) -> str:
        return jwt.encode(
            {'user_id': user_id, 'exp': datetime.now(pytz.UTC) + timedelta(days=1)},
            self.secret,
            algorithm='HS256'
        )
    
    def require_auth(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token or not token.startswith('Bearer '):
                return jsonify({'error': 'Missing token'}), 401
            try:
                token = token.split('Bearer ')[1]
                payload = jwt.decode(token, self.secret, algorithms=['HS256'])
                request.user_id = payload['user_id']
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                return jsonify({'error': 'Invalid token'}), 401
            return f(*args, **kwargs)
        return decorated

auth = AuthHandler()
x_client = XClient()

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        verified = robust_password_verify(user.password, password)
        
        if verified:
            token = auth.generate_token(user.id)
            return jsonify({'token': token})
        
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        app.logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Server error during login'}), 500

@app.route('/api/credentials', methods=['PUT'])
@auth.require_auth
def update_credentials():
    data = request.get_json()
    user = User.query.get(request.user_id)
    
    if not robust_password_verify(user.password, data['current_password']):
        return jsonify({'error': 'Invalid current password'}), 401
        
    user.password = robust_password_hash(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password updated'})

@app.route('/api/posts', methods=['GET', 'POST'])
@auth.require_auth
def manage_posts():
    if request.method == 'GET':
        posts = Post.query.filter_by(user_id=request.user_id).all()
        return jsonify([{
            'id': p.id,
            'content': p.content,
            'scheduled_time': p.eastern_scheduled_time,
            'status': p.status,
            'platform': p.platform,
            'post_id': p.post_id
        } for p in posts])
    
    data = request.get_json()
    app.logger.info(f"Received post data: {data}")
    
    try:
        scheduled_time = parse_iso_datetime(data['scheduled_time'])
        app.logger.info(f"Parsed scheduled time: {scheduled_time} UTC")
    except ValueError as e:
        app.logger.error(f"Failed to parse datetime: {str(e)}")
        return jsonify({'error': str(e)}), 400
        
    post = Post(
        content=data['content'],
        scheduled_time=scheduled_time,
        platform=data['platform'],
        user_id=request.user_id
    )
    
    # Set status based on scheduling
    if is_scheduled_time_future(post.scheduled_time):
        post.status = 'scheduled'
        app.logger.info(f"Post scheduled for future: {post.eastern_scheduled_time}")
    else:
        app.logger.info(f"Post scheduled for past/now: {post.eastern_scheduled_time}")
        if post.platform == 'x':
            result = x_client.post(post.content)
            if result['success']:
                post.post_id = result['post_id']
                post.status = 'posted'
            else:
                post.status = 'failed'
                return jsonify({'error': result['error']}), 500

    db.session.add(post)
    db.session.commit()
    return jsonify({
        'id': post.id,
        'status': post.status,
        'post_id': post.post_id
    }), 201

@app.route('/api/posts/<int:post_id>', methods=['GET', 'PUT', 'DELETE'])
@auth.require_auth
def manage_single_post(post_id):
    try:
        app.logger.info(f"Processing {request.method} request for post {post_id}")
        post = Post.query.get_or_404(post_id)
        
        if post.user_id != request.user_id:
            app.logger.warning(f"Unauthorized access attempt for post {post_id} by user {request.user_id}")
            return jsonify({'error': 'Unauthorized'}), 403

        if request.method == 'GET':
            return jsonify({
                'id': post.id,
                'content': post.content,
                'scheduled_time': format_datetime_for_response(post.scheduled_time),
                'status': post.status,
                'platform': post.platform,
                'post_id': post.post_id
            })

        elif request.method == 'PUT':
            data = request.get_json()
            app.logger.info(f"Update data received: {data}")

            if 'content' in data:
                post.content = data['content']
                app.logger.info(f"Updating content for post {post_id}")

            if 'scheduled_time' in data:
                try:
                    new_time = parse_iso_datetime(data['scheduled_time'])
                    post.scheduled_time = new_time
                    app.logger.info(f"Updating scheduled time for post {post_id} to {new_time}")
                except ValueError as e:
                    app.logger.error(f"Invalid datetime format: {data['scheduled_time']}")
                    return jsonify({'error': f'Invalid datetime format: {str(e)}'}), 400
            
            if data.get('status') == 'post_now':
                app.logger.info(f"Attempting immediate post for post {post_id}")
                if post.platform == 'x':
                    result = x_client.post(post.content)
                    if result['success']:
                        post.post_id = result['post_id']
                        post.status = 'posted'
                        app.logger.info(f"Successfully posted {post_id} to X")
                    else:
                        post.status = 'failed'
                        app.logger.error(f"Failed to post {post_id} to X: {result['error']}")
                        return jsonify({'error': result['error']}), 500
            elif is_scheduled_time_future(post.scheduled_time):
                post.status = 'scheduled'
                    
            db.session.commit()
            app.logger.info(f"Successfully updated post {post_id}")
            
            return jsonify({
                'message': 'Post updated',
                'status': post.status,
                'post_id': post.post_id
            })

        elif request.method == 'DELETE':
            app.logger.info(f"Deleting post {post_id}")
            db.session.delete(post)
            db.session.commit()
            app.logger.info(f"Successfully deleted post {post_id}")
            return '', 204

    except Exception as e:
        app.logger.error(f"Error handling {request.method} for post {post_id}: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_connection', methods=['GET'])
@auth.require_auth
def test_connection():
    result = x_client.post("Testing API connection from fore-poster")
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default user if none exists
        if not User.query.first():
            default_user = User(
                username='admin',
                password=robust_password_hash('admin')
            )
            db.session.add(default_user)
            db.session.commit()
            app.logger.info('Created default admin user')
    app.run(debug=True, port=8000)