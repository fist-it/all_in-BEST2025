from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

#obiekt bazy danych
db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) 

    def set_password(self, password):
        #zahaszowane haslo
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        #weryfikacja hasla
        return check_password_hash(self.password_hash, password)

def get_user_by_username(username):
    #funkcja do logowania (do main.py)
    return User.query.filter_by(username=username).first()