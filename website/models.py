# website/models.py 
# Classes for Users and Books
from datetime import datetime, timedelta
from flask_login import UserMixin
from website import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255), nullable=False)
    # Default role is student
    role = db.Column(db.String(20), nullable=False, default='student')  

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    is_checked_out = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime)
    borrower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    borrower = db.relationship('User', foreign_keys=[borrower_id])
    
    
    @property
    def is_overdue(self):
        return self.is_checked_out and self.due_date < datetime.utcnow()

    @property
    def calculate_fine(self):
        if self.is_overdue:
            overdue_days = (datetime.utcnow() - self.due_date).days
            # Adjust the fine calculation logic as needed
            fine_per_day = 2  # Example: $2 per day overdue
            return overdue_days * fine_per_day
        return 0