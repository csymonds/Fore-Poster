from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import jwt
import os
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import tweepy
from env_handler import load_environment, get_env_var
from functools import wraps
from config import Config
from datetime import datetime, timedelta
import pytz
import hashlib
import uuid
import os.path

CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:4173,http://localhost:3000').split(',')

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

def post_now_handler(post):
    """Handle immediate posting of a post.
    
    This function processes an immediate post request, including handling
    any attached images.
    
    Args:
        post: The Post object to publish
        
    Returns:
        JSON response with result information
    """
    app.logger.info(f"Processing immediate post for ID: {post.id}")
    
    if post.platform == 'x':
        # Check if post has an image
        image_path = None
        if post.image_filename:
            image_path = os.path.join(UPLOAD_FOLDER, post.image_filename)
            # Check if the image file exists
            if not os.path.exists(image_path):
                app.logger.warning(f"Image file not found: {image_path}")
                image_path = None
            else:
                app.logger.info(f"Including image: {post.image_filename}")
        
        # Post with or without image
        result = x_client.post(post.content, image_path)
        
        if result['success']:
            post.post_id = result['post_id']
            post.status = 'posted'
            db.session.commit()
            
            # Check if there was a warning about image upload
            if 'warning' in result:
                app.logger.warning(f"Post successful but with image warning: {result['warning']}")
                return jsonify({
                    'id': post.id,
                    'status': post.status,
                    'post_id': post.post_id,
                    'warning': result['warning']
                })
            
            return jsonify({
                'id': post.id,
                'status': post.status,
                'post_id': post.post_id
            })
        else:
            post.status = 'failed'
            db.session.commit()
            app.logger.error(f"Post failed: {result.get('error', 'Unknown error')}")
            return jsonify({'error': result.get('error', 'Failed to post')}), 500
    
    app.logger.error(f"Unsupported platform: {post.platform}")
    return jsonify({'error': f'Unsupported platform: {post.platform}'}), 400

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

# Load configuration
load_environment()
Config.init_app(os.getenv('APP_ENV', 'development'))
app.config.from_object(Config)

# Set up upload folder
upload_dir = os.getenv('UPLOAD_FOLDER', 'instance/uploads')
UPLOAD_FOLDER = os.path.join(app.instance_path, upload_dir.replace('instance/', ''))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Get allowed extensions from environment
allowed_extensions_str = os.getenv('ALLOWED_FILE_EXTENSIONS', 'png,jpg,jpeg,gif')
app.config['ALLOWED_EXTENSIONS'] = set(ext.strip() for ext in allowed_extensions_str.split(','))

# Set max content length from environment
max_upload_size = int(os.getenv('MAX_UPLOAD_SIZE_MB', '16'))
app.config['MAX_CONTENT_LENGTH'] = max_upload_size * 1024 * 1024  # Convert to bytes

# Cache duration for static files
CACHE_MAX_AGE = int(os.getenv('CACHE_MAX_AGE', '86400'))  # Default: 1 day

# Configure CORS using the environment variable
CORS(app, resources={r"/*": {"origins": CORS_ORIGINS}}, 
     supports_credentials=True, 
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

db = SQLAlchemy(app)

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.lower().split('.')[-1] in app.config['ALLOWED_EXTENSIONS']

def validate_image_content(file_stream):
    """Validate that the file contains actual image data by checking its header.
    
    Args:
        file_stream: A file-like object containing the image data
        
    Returns:
        bool: True if the file appears to be a valid image, False otherwise
    """
    # Save current position
    pos = file_stream.tell()
    
    # Read first 12 bytes for signature check
    header = file_stream.read(12)
    
    # Reset to initial position
    file_stream.seek(pos)
    
    # Check common image signatures
    if header.startswith(b'\xFF\xD8\xFF'):  # JPEG
        return True
    if header.startswith(b'\x89PNG\r\n\x1A\n'):  # PNG
        return True
    if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):  # GIF
        return True
        
    return False

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
    # New fields for image upload functionality
    image_filename = db.Column(db.String(255))  # Filename of uploaded image
    image_url = db.Column(db.String(500))  # URL of the image in our system

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
            # Initialize Tweepy client for Twitter API v2
            self.client = tweepy.Client(
                consumer_key=get_env_var('X_API_KEY'),
                consumer_secret=get_env_var('X_API_SECRET'),
                access_token=get_env_var('X_ACCESS_TOKEN'),
                access_token_secret=get_env_var('X_ACCESS_TOKEN_SECRET')
            )
            
            # Initialize Tweepy API v1.1 (needed for media uploads)
            auth = tweepy.OAuth1UserHandler(
                consumer_key=get_env_var('X_API_KEY'),
                consumer_secret=get_env_var('X_API_SECRET'),
                access_token=get_env_var('X_ACCESS_TOKEN'),
                access_token_secret=get_env_var('X_ACCESS_TOKEN_SECRET')
            )
            self.api = tweepy.API(auth)
            
            app.logger.info('X client initialized')
    
    def post(self, content: str, image_path: str = None) -> dict:
        """Post to X/Twitter, optionally with an image."""
        if self.test_mode:
            app.logger.info("Test mode: Skipping actual post")
            return {'success': True, 'post_id': 'test_123'}
            
        try:
            app.logger.info(f"Attempting to post to X: {content[:50]}...")
            
            # If an image is provided, upload it and include it in the tweet
            if image_path and os.path.exists(image_path):
                app.logger.info(f"Uploading image: {image_path}")
                try:
                    # Upload media using v1.1 API
                    media = self.api.media_upload(image_path)
                    media_id = media.media_id_string
                    app.logger.info(f"Successfully uploaded image with media_id: {media_id}")
                    
                    # Post tweet with media using v2 API
                    response = self.client.create_tweet(
                        text=content,
                        media_ids=[media_id]
                    )
                    app.logger.info(f"Successfully posted to X with image, post_id: {response.data['id']}")
                    return {'success': True, 'post_id': response.data['id']}
                except Exception as e:
                    app.logger.error(f"Error uploading image: {str(e)}")
                    # Fall back to text-only tweet if image upload fails
                    app.logger.info("Falling back to text-only tweet")
                    response = self.client.create_tweet(text=content)
                    app.logger.info(f"Posted text-only tweet, post_id: {response.data['id']}")
                    return {'success': True, 'post_id': response.data['id'], 'warning': 'Image upload failed'}
            else:
                # Standard text-only tweet
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
    """Log API response details without attempting to read file response bodies.
    
    This function logs API responses but handles file responses differently
    to avoid errors with Flask's direct_passthrough mode.
    """
    # Extract basic response info
    if response.status_code >= 400:
        # Only log detailed info for errors
        log_message = f"""
Response:
  Status: {response.status}
  Headers: {dict(response.headers)}"""
        
        # Only try to log the body for non-file responses
        if not getattr(response, 'direct_passthrough', False) and \
           not response.mimetype.startswith(('image/', 'video/', 'audio/')):
            try:
                body = response.get_data(as_text=True)
                # If body is too large, truncate it
                if len(body) > 500:
                    body = body[:500] + "... [truncated]"
                log_message += f"\n  Body: {body}"
            except Exception:
                log_message += "\n  Body: [Could not read response body]"
        else:
            log_message += "\n  Body: [File or binary data - not logged]"
            
        app.logger.warning(log_message)
    elif response.status_code >= 300:
        # Basic logging for redirects
        app.logger.info(f"Response: {response.status}")
    else:
        # Minimal logging for successful responses
        app.logger.info(f"Response: {response.status}")
        
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
        response_data = [{
            'id': p.id,
            'content': p.content,
            'scheduled_time': p.eastern_scheduled_time,
            'status': p.status,
            'platform': p.platform,
            'post_id': p.post_id,
            'image_url': p.image_url,
            'image_filename': p.image_filename
        } for p in posts]
        app.logger.info(f"Returning {len(posts)} posts")
        return jsonify(response_data)
    
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
        user_id=request.user_id,
        image_filename=data.get('image_filename'),
        image_url=data.get('image_url')
    )
    
    if post.image_url:
        app.logger.info(f"Post includes image: {post.image_filename}")
    
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
        'post_id': post.post_id,
        'image_url': post.image_url,
        'image_filename': post.image_filename
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
                'post_id': post.post_id,
                'image_url': post.image_url,
                'image_filename': post.image_filename
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            app.logger.info(f"Update data received: {data}")
            
            # Check for status=post_now special case
            if data.get('status') == 'post_now':
                app.logger.info(f"Posting now for post {post_id}")
                return post_now_handler(post)
                
            # Regular update
            if 'content' in data:
                post.content = data['content']
                
            if 'scheduled_time' in data:
                try:
                    post.scheduled_time = parse_iso_datetime(data['scheduled_time'])
                except ValueError as e:
                    app.logger.error(f"Failed to parse datetime: {str(e)}")
                    return jsonify({'error': str(e)}), 400
                    
            if 'platform' in data:
                post.platform = data['platform']
                
            if 'status' in data:
                post.status = data['status']
            
            # Handle image updates - explicitly handle null values
            if 'image_filename' in data:
                # If null is passed, clear the image filename
                if data['image_filename'] is None:
                    app.logger.info(f"Clearing image filename for post {post_id}")
                    post.image_filename = None
                else:
                    post.image_filename = data['image_filename']
            
            if 'image_url' in data:
                # If null is passed, clear the image URL
                if data['image_url'] is None:
                    app.logger.info(f"Clearing image URL for post {post_id}")
                    post.image_url = None
                else:
                    post.image_url = data['image_url']
            
            # Log whether we have an image after update
            if post.image_url:
                app.logger.info(f"Post updated with image: {post.image_filename}")
            else:
                app.logger.info("Post updated without image")
                
            db.session.commit()
            app.logger.info(f"Successfully updated post {post_id}")
            return jsonify({
                'id': post.id, 
                'status': post.status,
                'image_url': post.image_url,
                'image_filename': post.image_filename
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

# Create a direct file endpoint that avoids using Flask's built-in static handler
@app.route('/files/<path:filename>', methods=['GET', 'OPTIONS'])
def serve_uploaded_file(filename):
    """Serve uploaded files from the uploads directory.
    
    This endpoint serves files directly without authentication to allow
    browsers to load images without CORS issues.
    
    Args:
        filename: The name of the file to serve
        
    Returns:
        The file response or an error JSON
    """
    if request.method == 'OPTIONS':
        # CORS preflight handling is done by Flask-CORS extension
        return app.make_default_options_response()
        
    try:
        # Prevent directory traversal attacks
        if '..' in filename or filename.startswith('/'):
            app.logger.warning(f"Possible directory traversal attempt: {filename}")
            return jsonify({'error': 'Invalid filename'}), 400
            
        # Additional validation - ensure the file path is within the uploads directory
        file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, filename))
        if not file_path.startswith(os.path.abspath(UPLOAD_FOLDER)):
            app.logger.warning(f"Path traversal attempt detected: {filename}")
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if file exists before trying to serve it
        if not os.path.isfile(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Serve the file with caching headers
        response = send_from_directory(UPLOAD_FOLDER, filename, conditional=True)
        response.headers.add('Cache-Control', f'public, max-age={CACHE_MAX_AGE}')
        
        return response
    except Exception as e:
        app.logger.error(f"Error serving file {filename}: {str(e)}", exc_info=True)
        return jsonify({'error': f"Error serving file: {str(e)}"}), 500

# Handle file uploads
@app.route('/api/upload', methods=['POST', 'OPTIONS'])
@auth.require_auth
def upload_file():
    """Upload a file and return its URL."""
    # Handle preflight CORS requests
    if request.method == 'OPTIONS':
        return app.make_default_options_response()
        
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Additional content-based validation
            if not validate_image_content(file.stream):
                app.logger.warning(f"Invalid image content detected: {file.filename}")
                return jsonify({'error': 'Invalid image file'}), 400
            
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # Save the file
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            # Generate URL for the file - use request.host_url to get the actual server URL
            base_url = request.host_url.rstrip('/')
            file_url = f"{base_url}/files/{unique_filename}"
            
            app.logger.info(f"File saved: {unique_filename}")
            
            return jsonify({
                'filename': unique_filename,
                'url': file_url,
                'original_filename': original_filename
            }), 201
        
        return jsonify({'error': 'File type not allowed'}), 400
    
    except Exception as e:
        app.logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

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