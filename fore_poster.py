from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
import os
from datetime import datetime, timedelta
import hashlib
import tweepy
from env_handler import get_env_var
from functools import wraps
from config import Config

app = Flask(__name__)
Config.init_app(os.getenv('FLASK_ENV', 'development'))
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, posted, failed
    platform = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.String(120))  # Store platform post ID after posting

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
    
    def post(self, content: str) -> dict:
        if self.test_mode:
            print("Test mode: Skipping actual post")
            return {'success': True, 'post_id': 'test_123'}
            
        try:
            response = self.client.create_tweet(text=content)
            return {'success': True, 'post_id': response.data['id']}
        except Exception as e:
            return {'success': False, 'error': str(e)}

class AuthHandler:
    def __init__(self):
        self.secret = get_env_var('JWT_SECRET')
        if not self.secret:
            raise EnvironmentError("JWT_SECRET environment variable is required")
            
    def generate_token(self, user_id: int) -> str:
        return jwt.encode(
            {'user_id': user_id, 'exp': datetime.utcnow() + timedelta(days=1)},
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
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.password == hashlib.sha256(data['password'].encode()).hexdigest():
        return jsonify({'token': auth.generate_token(user.id)})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/credentials', methods=['PUT'])
@auth.require_auth
def update_credentials():
    data = request.get_json()
    user = User.query.get(request.user_id)
    
    if not user.password == hashlib.sha256(data['current_password'].encode()).hexdigest():
        return jsonify({'error': 'Invalid current password'}), 401
        
    user.password = hashlib.sha256(data['new_password'].encode()).hexdigest()
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
            'scheduled_time': p.scheduled_time.isoformat(),
            'status': p.status,
            'platform': p.platform,
            'post_id': p.post_id
        } for p in posts])
    
    data = request.get_json()
    post = Post(
        content=data['content'],
        scheduled_time=datetime.fromisoformat(data['scheduled_time']),
        platform=data['platform'],
        user_id=request.user_id
    )
    
    # Set status based on scheduling
    if post.scheduled_time > datetime.utcnow():
        post.status = 'scheduled'
    else:
        # Post immediately if scheduled time is now or past
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
    post = Post.query.get_or_404(post_id)
    if post.user_id != request.user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    if request.method == 'GET':
        return jsonify({
            'id': post.id,
            'content': post.content,
            'scheduled_time': post.scheduled_time.isoformat(),
            'status': post.status,
            'platform': post.platform,
            'post_id': post.post_id
        })

    elif request.method == 'PUT':
        data = request.get_json()
        post.content = data.get('content', post.content)
        new_time = data.get('scheduled_time', post.scheduled_time.isoformat())
        post.scheduled_time = datetime.fromisoformat(new_time)
        
        if data.get('status') == 'post_now':
            if post.platform == 'x':
                result = x_client.post(post.content)
                if result['success']:
                    post.post_id = result['post_id']
                    post.status = 'posted'
                else:
                    post.status = 'failed'
                    return jsonify({'error': result['error']}), 500
        elif post.scheduled_time > datetime.utcnow():
            post.status = 'scheduled'
                
        db.session.commit()
        return jsonify({
            'message': 'Post updated',
            'status': post.status,
            'post_id': post.post_id
        })

    elif request.method == 'DELETE':
        db.session.delete(post)
        db.session.commit()
        return '', 204

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
                password=hashlib.sha256('admin'.encode()).hexdigest()
            )
            db.session.add(default_user)
            db.session.commit()
    app.run(debug=True)