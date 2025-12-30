import pytest
from app import app, db, User, Contact, bcrypt


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test users
            user1 = User(
                username='testuser',
                password=bcrypt.generate_password_hash('password123').decode('utf-8')
            )
            user2 = User(
                username='Ahmed',
                password=bcrypt.generate_password_hash('ahmed123').decode('utf-8')
            )
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()


def test_index_redirect(client):
    """Test that index redirects to login."""
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.location


def test_login_page_loads(client):
    """Test that login page loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data or b'login' in response.data


def test_login_success(client):
    """Test successful login."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid credentials' in response.data or b'invalid' in response.data.lower()


def test_contact_page_requires_login(client):
    """Test that contact page requires authentication."""
    response = client.get('/contact')
    assert response.status_code == 302
    assert '/login' in response.location


def test_contact_page_with_login(client):
    """Test that contact page loads when logged in."""
    # Login first
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    response = client.get('/contact')
    assert response.status_code == 200
    assert b'Contact' in response.data or b'contact' in response.data


def test_contact_form_submission(client):
    """Test contact form submission."""
    # Login first
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    response = client.post('/contact', data={
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890',
        'message': 'This is a test message for the contact form.'
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_logout(client):
    """Test logout functionality."""
    # Login first
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out' in response.data.lower() or b'logout' in response.data.lower()


def test_sql_injection_prevention(client):
    """Test SQL injection prevention in login."""
    response = client.post('/login', data={
        'username': "admin' OR '1'='1",
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid characters or keywords detected' in response.data or b'Invalid' in response.data


def test_xss_prevention(client):
    """Test XSS prevention in forms."""
    # Login first
    client.post('/login', data={
        'username': 'testuser',
        'password': 'password123'
    })
    
    response = client.post('/contact', data={
        'name': '<script>alert("XSS")</script>',
        'email': 'test@example.com',
        'phone': '+1234567890',
        'message': 'This is a test message.'
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_database_user_creation():
    """Test user creation in database."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        user = User(
            username='newuser',
            password=bcrypt.generate_password_hash('newpass123').decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()
        
        found_user = User.query.filter_by(username='newuser').first()
        assert found_user is not None
        assert found_user.username == 'newuser'
        
        db.drop_all()
