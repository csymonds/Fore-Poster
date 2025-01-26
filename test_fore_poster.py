import pytest
from datetime import datetime, timedelta
from fore_poster import app, db, User, XClient
from fore_scheduler import NotificationHandler
from unittest.mock import patch
import hashlib

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_fore_poster.db'
    
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            user = User(username='admin', password=hashlib.sha256('admin'.encode()).hexdigest())
            db.session.add(user)
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def auth_token(client):
    response = client.post('/api/login', json={'username': 'admin', 'password': 'admin'})
    return response.json['token']

@pytest.fixture
def mock_x_post(monkeypatch):
    def mock_post(*args, **kwargs):
        return {'success': True, 'post_id': 'test_123'}
    monkeypatch.setattr(XClient, 'post', mock_post)

def test_login(client):
    response = client.post('/api/login', json={'username': 'admin', 'password': 'admin'})
    assert response.status_code == 200
    assert 'token' in response.json

def test_get_posts(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.get('/api/posts', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_create_post(client, auth_token, mock_x_post):
    headers = {'Authorization': f'Bearer {auth_token}'}
    post_data = {
        'content': 'Test post',
        'scheduled_time': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        'platform': 'x'
    }
    response = client.post('/api/posts', headers=headers, json=post_data)
    assert response.status_code == 201
    assert 'id' in response.json
    return response.json['id']

def test_update_post(client, auth_token, mock_x_post):
    post_id = test_create_post(client, auth_token, mock_x_post)
    headers = {'Authorization': f'Bearer {auth_token}'}
    update_data = {
        'content': 'Updated test post',
        'scheduled_time': (datetime.utcnow() + timedelta(hours=2)).isoformat()
    }
    response = client.put(f'/api/posts/{post_id}', headers=headers, json=update_data)
    assert response.status_code == 200

def test_delete_post(client, auth_token, mock_x_post):
    post_id = test_create_post(client, auth_token, mock_x_post)
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = client.delete(f'/api/posts/{post_id}', headers=headers)
    assert response.status_code == 204

def test_update_credentials(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    data = {
        'current_password': 'admin',
        'new_password': 'newadmin'
    }
    response = client.put('/api/credentials', headers=headers, json=data)
    assert response.status_code == 200

def test_scheduled_post_creation(client, auth_token):
    headers = {'Authorization': f'Bearer {auth_token}'}
    future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    post_data = {
        'content': 'Future scheduled post',
        'scheduled_time': future_time,
        'platform': 'x'
    }
    response = client.post('/api/posts', headers=headers, json=post_data)
    print(f"Response status: {response.status_code}")
    print(f"Response text: {response.data}")  # Flask test client uses .data instead of .text
    assert response.status_code == 201
    assert response.json['status'] == 'scheduled'

def test_immediate_post_creation(client, auth_token, mock_x_post):
    headers = {'Authorization': f'Bearer {auth_token}'}
    current_time = datetime.utcnow().isoformat()
    post_data = {
        'content': 'Immediate post',
        'scheduled_time': current_time,
        'platform': 'x'
    }
    response = client.post('/api/posts', headers=headers, json=post_data)
    assert response.status_code == 201
    assert response.json['status'] == 'posted'
    assert response.json['post_id'] == 'test_123'

def test_post_now_command(client, auth_token, mock_x_post):
    headers = {'Authorization': f'Bearer {auth_token}'}
    future_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    post_data = {
        'content': 'Post now test',
        'scheduled_time': future_time,
        'platform': 'x'
    }
    create_response = client.post('/api/posts', headers=headers, json=post_data)
    post_id = create_response.json['id']
    
    update_data = {'status': 'post_now'}
    response = client.put(f'/api/posts/{post_id}', headers=headers, json=update_data)
    assert response.status_code == 200
    assert response.json['status'] == 'posted'
    assert response.json['post_id'] == 'test_123'

@pytest.fixture
def mock_ses():
    with patch('boto3.client') as mock:
        yield mock

def test_notification_dev_mode(caplog):
    with patch('fore_scheduler.Config') as mock_config:
        mock_config.PRODUCTION = False
        mock_config.DEVELOPMENT = True
        
        handler = NotificationHandler()
        handler.send_notification("Test Subject", "Test Message")
        assert "Development mode - would send email: Test Subject" in caplog.text
        
if __name__ == '__main__':
    pytest.main([__file__])