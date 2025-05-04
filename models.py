from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    reset_token = db.Column(db.String(200), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationship to financial goals
    goals = db.relationship('FinancialGoal', backref='user', lazy=True, cascade="all, delete-orphan")

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def set_password(self, password):
        """Set a new password for the user"""
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

class FinancialGoal(db.Model):
    __tablename__ = 'financial_goals'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    # Store timeframe as integer corresponding to frontend options
    timeframe = db.Column(db.Integer, nullable=False)  # 1=1 month, 2=3 months, 3=6 months, 4=1 year, 5=5+ years
    completed = db.Column(db.Boolean, default=False)
    target_amount = db.Column(db.Float, nullable=True)  # Optional target amount for the goal
    current_amount = db.Column(db.Float, default=0.0)   # Optional current progress amount
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key relationship with User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f"<FinancialGoal {self.title}>"
    
    def to_dict(self):
        """Convert goal object to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'timeframe': self.timeframe,
            'completed': self.completed,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }