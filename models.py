from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Obiekt bazy danych
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) 
    # Relacja do eventów
    events = db.relationship('Event', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Podstawowe info
    title = db.Column(db.String(150), nullable=False)
    location_name = db.Column(db.String(200), nullable=False)
    
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # Logika Live/Static
    event_type = db.Column(db.String(20), default='live') 
    
    date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    
    upvote_count = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    vote_type = db.Column(db.String(10)) # 'up' lub 'down'
    
    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='_user_event_uc'),)