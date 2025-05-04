from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import bcrypt
import os
from datetime import datetime

# Create a Flask app
app = Flask(__name__)

# Configure SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'
serializer = URLSafeTimedSerializer(app.secret_key)

# Initialize the database
db = SQLAlchemy(app)

#database management
class FinancialGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    timeframe = db.Column(db.Integer, nullable=False)  # e.g. 1=1 month, etc.
    completed = db.Column(db.Boolean, default=False)
    user_email = db.Column(db.String(50), db.ForeignKey('user__authentication.email'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'timeframe': self.timeframe,
            'completed': self.completed,
            'user_email': self.user_email,
            'created_at': self.created_at.isoformat()
        }
# Authentication
class User_Authentication(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
    def __init__(self, email, password, name):
        self.uname = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('know.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        
        user = User_Authentication.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['name'] = user.uname  # Store username in session
            session['email'] = user.email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid email or password")
        
    return render_template('login.html')


@app.route('/goals', methods=['GET'])
def goals_page():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['name'])


from flask import jsonify

@app.route('/add-goal', methods=['POST'])
def add_goal():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    title = data['title']
    timeframe = int(data['timeframe'])

    user = User_Authentication.query.filter_by(email=session['email']).first()
    new_goal = FinancialGoal(title=title, timeframe=timeframe, user_id=user.sno)
    db.session.add(new_goal)
    db.session.commit()

    return jsonify({'message': 'Goal added successfully'})

@app.route('/get-goals', methods=['GET'])
def get_goals():
    if 'email' not in session:
        return jsonify([])

    user = User_Authentication.query.filter_by(email=session['email']).first()
    goals = FinancialGoal.query.filter_by(user_id=user.sno).all()
    return jsonify([goal.to_dict() for goal in goals])

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    error = None
    success = None
    if request.method == 'POST':
        email = request.form['email']
        user = User_Authentication.query.filter_by(email=email).first()
        
        if not user:
            error = "No account found with that email address"
        else:
            # Generate a secure token
            token = serializer.dumps(email, salt='password-reset-salt')
            
            # Save token to user record
            user.reset_token = token
            user.reset_token_expiry = datetime.now().replace(microsecond=0)
            db.session.commit()
            
            # Create password reset link
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send email
            try:
                msg = Message('FinPlanner Password Reset Request', 
                             recipients=[email])
                msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email and no changes will be made.

This link will expire in 30 minutes.
'''
                mail.send(msg)
                success = "Password reset instructions sent to your email"
            except Exception as e:
                error = "Could not send reset email. Please try again later."
                app.logger.error(f"Email send error: {str(e)}")
    
    return render_template('forgot_password.html', error=error, success=success)

# Reset password route
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    error = None
    
    try:
        # Verify token (expires after 30 minutes)
        email = serializer.loads(token, salt='password-reset-salt', max_age=1800)
        user = User_Authentication.query.filter_by(email=email, reset_token=token).first()
        
        if not user:
            return render_template('reset_expired.html')
        
        if request.method == 'POST':
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            if password != confirm_password:
                error = "Passwords don't match"
            elif len(password) < 6:
                error = "Password must be at least 6 characters long"
            else:
                # Update password
                user.set_password(password)
                user.reset_token = None
                user.reset_token_expiry = None
                db.session.commit()
                
                flash('Your password has been updated! You can now log in with your new password.', 'success')
                return redirect(url_for('login'))
        
        return render_template('reset_password.html', token=token, error=error)
    
    except SignatureExpired:
        return render_template('reset_expired.html', error="The password reset link has expired")
    except BadSignature:
        return render_template('reset_expired.html', error="Invalid reset link")

# Handle POST-refresh issues with Post/Redirect/Get pattern
@app.after_request
def add_header(response):
    if response.status_code == 200 and request.method == "POST":
        if request.path in ['/login', '/signup', '/forgot-password']:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
    return response

# Create a simple template for expired reset links
@app.route('/reset-expired')
def reset_expired():
    return render_template('reset_expired.html')

@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username already exists
        existing_username = User_Authentication.query.filter_by(uname=name).first()
        if existing_username:
            return render_template('sign_up.html', error="Username already taken")
        
        # Check if email already exists
        existing_email = User_Authentication.query.filter_by(email=email).first()
        if existing_email:
            return render_template('sign_up.html', error="Email already registered")
        
        try:
            new_user = User_Authentication(email=email, password=password, name=name)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            return render_template('sign_up.html', error=f"Registration failed: {str(e)}")
    
    return render_template('sign_up.html')

@app.route('/dashboard')
def dashboard():
    if 'name' in session:
        return render_template('dashboard.html', username=session['name'])
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)