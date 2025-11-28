import os
import json
from datetime import datetime, timedelta, UTC
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash # hashowanie
from google import genai
from models import db, User, Event, Vote, get_user_by_username
from geopy.geocoders import Nominatim

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

MAX_FUTURE_VISIBILITY = timedelta(hours=1) # Max czas w przyszłość
TIME_EXTENSION = timedelta(minutes=30)

@login_manager.user_loader
def load_user(user_id):
    # ładowanie z db
    return db.session.get(User, int(user_id))

with app.app_context():
    #site.db i tabele
    db.create_all()

geolocator = Nominatim(user_agent="my_best_app_2025")

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

#==
#API: Facebook Events
#==

@app.route('/api/events/fb')
# @login_required # - Disabled for API development
def api_events_fb():
    EVENTS_FILE = "data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668-formatted.json"
    try:
        if not os.path.exists(EVENTS_FILE):
            return jsonify({})

        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        city_query = request.args.get('city')
        if city_query:
            data = [
                item for item in data 
                if item.get('location.city') and city_query.lower() in item['location.city'].lower()
            ]
        return jsonify(data)
        
    except Exception as e:
        return jsonify({})

@app.route('/api/events/user')
# @login_required # - Disabled for API development
def api_events_user():
    db_events = Event.query.all()
    output_list = []
    
    for event in db_events:
        if event.latitude and event.longitude:
            event_dict = {
                "id": event.id,
                "name": event.title,
                "location.name": event.location_name,
                "location.city": "Gdańsk", 
                "location.countryCode": "PL", 
                "utcStartDate": event.date, 
                "latitude": event.latitude,
                "longitude": event.longitude,
                "source": "User",
                "event_type": event.event_type,
                "upvoteCount": event.upvote_count,
                "is_mine": current_user.is_authenticated and event.user_id == current_user.id
            }
            output_list.append(event_dict)

    return jsonify(output_list)

#==
#API: Reports CRUD
#==

# @login_required # - Disabled for API development
# przykładowe dane tak +-:
#   {
#       "category": "live"/"static",
#       "name": "AAA",
#       "utcStartDate": "2025-10-12T10:00:00.000Z",
#       "utcEndDate": "2025-10-12T10:00:00.000Z", # użytkownik może zrobić +/-, - informuje że nie ma już np. ziutka z gitarą, + informuje że jest i wydłuża np. o 1h
#       "upvoteCount": 0,
#       "latitude": 0.0,
#       "longitude": 0.0,
#   }
#
# jeżeli category=static to danie downvote po prostu jakoś się odznacza
# jeżeli cateogory=live to danie downvote oznacza wydarzenie na mapie jako zakończone 
@app.route('/api/add_event', methods=['POST'])
def add_event():
    if request.method == 'POST':
        title = request.form.get('title')
        user_event_type = request.form.get('type')
        
        raw_lat = request.form.get('latitude')
        raw_lng = request.form.get('longitude')
        
        # Opcjonalna nazwa własna (np. "nig z Papieżem")
        location_input = request.form.get('location_name') 

        lat, lng = None, None
        final_location_name = location_input

        # walidacja i reverse Geocoding
        if raw_lat and raw_lng:
            try:
                lat = float(raw_lat)
                lng = float(raw_lng)
                
                if not final_location_name:
                    try:
                        location_data = geolocator.reverse(f"{lat}, {lng}", timeout=5)
                        if location_data:
                            final_location_name = location_data.address
                        else:
                            final_location_name = f"Lokalizacja: {lat:.3f}, {lng:.3f}"
                    except:
                        final_location_name = "Nieznany adres"
                        print("Błąd reverse geocoding")
            except ValueError:
                return jsonify({"error": "Nieprawidłowy format współrzędnych"}), 400
        else:
            return jsonify({"error": "Musisz zaznaczyć miejsce na mapie!"}), 400

        if not final_location_name:
            final_location_name = "Zaznaczone miejsce"

        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        default_end = now + timedelta(hours=1)

        if current_user.is_authenticated:
            event_author = current_user
        else:
            return jsonify({"error": "Musisz być zalogowany"}), 401

        new_event = Event(
            title=title,
            date=now,
            end_date=default_end,
            event_type=user_event_type or 'live',
            location_name=final_location_name, # Tu wpadnie adres wyliczony przez geopy lub wpisany przez usera
            latitude=lat,
            longitude=lng,
            author=event_author
        )

        db.session.add(new_event)
        db.session.commit()
        
        # Przekierowanie na stronę główną
        return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/api/delete_event/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    event = db.session.get(Event, event_id)
    
    if not event:
        print("BŁĄD: Nie znaleziono eventu o tym ID")
        return jsonify({'error': 'Event not found'}), 404

    print(f"DEBUG: Event ID: {event.id}, Owner ID: {event.user_id}, Current User ID: {current_user.id}")

    if event.user_id == current_user.id:
        try:
            db.session.delete(event)
            db.session.commit()
            print("SUKCES: Usunięto z bazy")
            return jsonify({'message': 'Deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            print(f"BŁĄD BAZY: {e}")
            return jsonify({'error': str(e)}), 500
    else:
        print("BŁĄD: Brak uprawnień (to nie Twój event)")
        return jsonify({'error': 'Unauthorized'}), 403

@app.route('/api/vote', methods=['POST'])
def vote_event():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Musisz być zalogowany, aby głosować'}), 401

    data = request.json
    event_id = data.get('event_id')
    vote_type = data.get('vote')
    
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    existing_vote = Vote.query.filter_by(user_id=current_user.id, event_id=event_id).first()

    if existing_vote:
        return jsonify({'error': 'Już oddałeś głos na to wydarzenie!'}), 400
        
    new_vote = Vote(user_id=current_user.id, event_id=event.id, vote_type=vote_type)
    db.session.add(new_vote)

    if event.event_type == 'live':        
        now = datetime.now(UTC) # timezone aware
        hard_cap = now + MAX_FUTURE_VISIBILITY

        if vote_type == 'up':
            event.upvote_count += 1
            if event.end_date.replace(tzinfo=UTC) < now: # strefy czasowe fix
                event.end_date = now + TIME_EXTENSION
            else:
                proposed_end_date = event.end_date.replace(tzinfo=UTC) + TIME_EXTENSION
                if proposed_end_date > hard_cap:
                    event.end_date = hard_cap
                else:
                    event.end_date = proposed_end_date

        elif vote_type == 'down':
            event.upvote_count -= 1
            event.end_date = event.end_date.replace(tzinfo=UTC) - TIME_EXTENSION
        
            if event.upvote_count < -5:
                event.end_date = now

    else: # STATIC
        if vote_type == 'up':
            event.upvote_count += 1
        elif vote_type == 'down':
            event.upvote_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Błąd zapisu głosu'}), 500
    
    return jsonify({
        'new_score': event.upvote_count, 
        'new_end_date': event.end_date.isoformat(),
        'message': 'Głos zapisany'
    })

@app.route('/api/events', methods=['GET'])
# @login_required # - Disabled for API development
def api_events():
    all_events = []

    # Scraped data
    
    # User data
    db_events = Event.query.all()
    for event in db_events:
        if event.latitude and event.longitude:
            all_events.append({
                "id": event.id,
                "name": event.title,
                "location.name": event.location_name,
                "location.city": "Gdańsk",
                "location.countryCode": "PL", 
                "utcStartDate": event.date,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "source": "User",
                "is_mine": current_user.is_authenticated and event.user_id == current_user.id
            })

    return jsonify(all_events)

if __name__ == '__main__':
    main()
