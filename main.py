import os
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash # hashowanie
from google import genai
from models import db, User, get_user_by_username #baza danych

def main():
    #w trybie developerskim
    app.run(debug=True)


#flask, login, db
app = Flask(__name__)
app.config['SECRET_KEY'] = 'bardzo_tajny_klucz_dla_flask_login' 

#bd SQLite - site.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app) # db init
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    # ładowanie z db
    return db.session.get(User, int(user_id))

with app.app_context():
    #site.db i tabele
    db.create_all()

#======
#WIDOKI
#======

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if get_user_by_username(username):
            error = 'Użytkownik o tej nazwie już istnieje.'
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            login_user(new_user)
            return redirect(url_for('index'))
            
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = get_user_by_username(username)

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = 'Błędny login lub hasło'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required 
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/')
@login_required
def index():
    return render_template('index.html')


if __name__ == '__main__':
    main()
