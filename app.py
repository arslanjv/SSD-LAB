from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect, FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError, Regexp , Email
from datetime import datetime
import re
import os

app = Flask(__name__)

# Security configurations
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(32))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['WTF_CSRF_TIME_LIMIT'] = None

db = SQLAlchemy(app)
csrf = CSRFProtect(app)
bcrypt = Bcrypt(app)

# Custom validators
def validate_no_sql_injection(form, field):
    sql_keywords = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 
        'ALTER', 'EXEC', 'UNION', 'SCRIPT', '--', ';', '/*', '*/',
        'xp_', 'sp_', 'OR', 'AND', '1=1', '1 = 1'
    ]
    data_upper = field.data.upper()
    for keyword in sql_keywords:
        # Match only whole words or special sequences
        if re.search(r'\b' + re.escape(keyword) + r'\b', data_upper):
            raise ValidationError('Invalid characters or keywords detected')

def validate_no_xss(form, field):
    dangerous_chars = ['<script>', '</script>', '<iframe>', 'javascript:', 
                      'onerror=', 'onload=', '<img', '<object>']
    data_lower = field.data.lower()
    for char in dangerous_chars:
        if char in data_lower:
            raise ValidationError('Invalid HTML or script content detected')

def validate_phone(form, field):
    phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]{10,20}$')
    if not phone_pattern.match(field.data):
        raise ValidationError('Invalid phone number format')

# Forms with validation
class LoginForm(FlaskForm):
    username = StringField('Username', 
                          validators=[
                              DataRequired(message='Username is required'),
                              Length(min=3, max=80, message='Username must be 3-80 characters'),
                              validate_no_sql_injection,
                              validate_no_xss
                          ])
    password = PasswordField('Password',
                           validators=[
                               DataRequired(message='Password is required'),
                               Length(min=6, message='Password must be at least 6 characters')
                           ])

class ContactForm(FlaskForm):
    name = StringField('Name',
                      validators=[
                          DataRequired(message='Name is required'),
                          Length(min=2, max=100, message='Name must be 2-100 characters'),
                          validate_no_sql_injection,
                          validate_no_xss
                      ])
    email = StringField('Email',
                       validators=[
                           DataRequired(message='Email is required'),
                           Email(message='Invalid email address'),
                           validate_no_sql_injection
                       ])
    phone = StringField('Phone',
                       validators=[
                           DataRequired(message='Phone is required'),
                           validate_phone,
                           validate_no_sql_injection
                       ])
    message = TextAreaField('Message',
                           validators=[
                               DataRequired(message='Message is required'),
                               Length(min=10, max=1000, message='Message must be 10-1000 characters'),
                               validate_no_sql_injection,
                               validate_no_xss
                           ])

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contacts = db.relationship('Contact', backref='user', lazy=True, cascade='all, delete-orphan')

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        
        # Parameterized query via SQLAlchemy ORM
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session.permanent = True
            flash('Login successful', 'success')
            return redirect(url_for('contact'))
        else:
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html', form=form)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    form = ContactForm()
    
    if form.validate_on_submit():
        # Parameterized insert via SQLAlchemy ORM
        new_contact = Contact(
            user_id=session['user_id'],
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            phone=form.phone.data.strip(),
            message=form.message.data.strip()
        )
        
        try:
            db.session.add(new_contact)
            db.session.commit()
            flash('Contact message submitted successfully', 'success')
            return redirect(url_for('contact'))
        except Exception:
            db.session.rollback()
            flash('An error occurred. Please try again', 'error')
            return redirect(url_for('contact'))
    
    return render_template('contact.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

def init_db():
    with app.app_context():
        # Drop all tables and recreate to ensure clean state
        db.drop_all()
        db.create_all()
        
        # Create users with bcrypt hashed passwords
        ahmed = User(
            username='Ahmed',
            password=bcrypt.generate_password_hash('ahmed123').decode('utf-8')
        )
        db.session.add(ahmed)
        print("Created user: Ahmed (password: ahmed123)")
        
        umer = User(
            username='Umer',
            password=bcrypt.generate_password_hash('umer123').decode('utf-8')
        )
        db.session.add(umer)
        print("Created user: Umer (password: umer123)")
        
        db.session.commit()
        print("\nDatabase initialized successfully")
        print("Login with: Ahmed/ahmed123 or Umer/umer123")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)