import os
import json
from datetime import datetime, timedelta, UTC
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash # hashowanie
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional
from models import db, User, Event, Vote, get_user_by_username
from geopy.geocoders import Nominatim
import datetime

try:
    if os.getenv("GEMINI_API_KEY") is None:
        print("brak GEMINI_API_KEY w zmiennych srodowiskowych")
        client = None 
    else:
        client = genai.Client()
        print("chatbot aktywny")
except Exception as e:
    print(f"Błąd inicjalizacji klienta AI: {e}")
    client = None

def main():
    #w trybie developerskim
    app.run(debug=False, host='0.0.0.0')

def load_facebook_events(nazwa_pliku="dane.json"):
    if not os.path.exists(nazwa_pliku):
        return None
    try:
        with open(nazwa_pliku, 'r', encoding='utf-8') as plik:
            dane_json = json.load(plik)
            string_json = json.dumps(dane_json, indent=4, ensure_ascii=False)
            return string_json        
    except Exception:
        return None



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
                "utcEndDate": event.end_date, 
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
# @login_required # - Disabled for API development
def add_event():
    if not current_user.is_authenticated:
        return jsonify({"error": "Musisz być zalogowany, aby dodać zdarzenie!"}), 401

    if request.method == 'POST':
        title = request.form.get('title')
        user_event_type = request.form.get('type')
        raw_lat = request.form.get('latitude')
        raw_lng = request.form.get('longitude')
        location_input = request.form.get('location_name') 

        lat, lng = None, None
        final_location_name = location_input

        if raw_lat and raw_lng:
            try:
                lat = float(raw_lat)
                lng = float(raw_lng)
                
                if not final_location_name:
                    try:
                        location_data = geolocator.reverse(f"{lat}, {lng}", timeout=5)
                        final_location_name = location_data.address if location_data else f"{lat:.3f}, {lng:.3f}"
                    except:
                        final_location_name = "Nieznany adres"
            except ValueError:
                return jsonify({"error": "Błąd danych współrzędnych"}), 400
        else:
            return jsonify({"error": "Brak współrzędnych!"}), 400

        if not final_location_name:
            final_location_name = "Zaznaczone miejsce"

        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        default_end = now + timedelta(hours=1)

        new_event = Event(
            title=title,
            date=now,
            end_date=default_end,
            event_type=user_event_type or 'live',
            location_name=final_location_name,
            latitude=lat,
            longitude=lng,
            author=current_user
        )

        try:
            db.session.add(new_event)
            db.session.commit()
            
            return jsonify({
                "message": "Dodano pomyślnie!",
                "event": {
                    "id": new_event.id,
                    "title": new_event.title,
                    "lat": new_event.latitude,
                    "lng": new_event.longitude
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Method not allowed"}), 405

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
# @login_required # - Disabled for API development
def vote_event():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Musisz być zalogowany!'}), 401

    data = request.json
    event_id = data.get('event_id')
    vote_type = data.get('vote') # 'up' lub 'down'
    
    event = db.session.get(Event, event_id)
    if not event:
        return jsonify({'error': 'Event nie istnieje'}), 404

    existing_vote = Vote.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if existing_vote:
        return jsonify({'error': 'Już oddałeś głos na to zgłoszenie!'}), 400

    new_vote = Vote(user_id=current_user.id, event_id=event_id, vote_type=vote_type)
    db.session.add(new_vote)

    if event.event_type == 'live':
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        # Obliczamy Hard Cap (np. max 3h od teraz)
        hard_cap = now + MAX_FUTURE_VISIBILITY 

        if event.end_date.tzinfo is None:
            event.end_date = event.end_date.replace(tzinfo=timezone.utc)

        if vote_type == 'up':
            event.upvote_count += 1
            
            # Jeśli wygasło -> Ożywiamy
            if event.end_date < now:
                event.end_date = now + TIME_EXTENSION
            else:
                proposed_end = event.end_date + TIME_EXTENSION
                event.end_date = min(proposed_end, hard_cap)

        elif vote_type == 'down':
            event.upvote_count -= 1
            event.end_date -= TIME_EXTENSION
            
            if event.upvote_count <= -1:
                event.end_date = now

    else:
        if vote_type == 'up':
            event.upvote_count += 1
        elif vote_type == 'down':
            event.upvote_count -= 1
            if event.upvote_count <= -10:
                db.session.delete(event)

    try:
        db.session.commit()
        return jsonify({
            'new_score': event.upvote_count,
            'message': 'Głos zapisany'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/delete_event/<int:event_id>', methods=['DELETE'])
# @login_required # - Disabled for API development
def delete_event_api(event_id):
    if not current_user.is_authenticated:
        return jsonify({'error': 'Musisz być zalogowany'}), 401

    event = db.session.get(Event, event_id)
    
    if not event:
        return jsonify({'error': 'Wydarzenie nie istnieje'}), 404

    if event.user_id != current_user.id:
        return jsonify({'error': 'Nie masz uprawnień do usunięcia tego zgłoszenia'}), 403

    try:
        Vote.query.filter_by(event_id=event.id).delete() 
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Usunięto pomyślnie'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 50

@app.route('/api/chat', methods=['POST'])
@login_required
def handle_chat():
    user_message = request.json.get('message')
    czas = datetime.datetime.now()

    if client is None:
        ai_response = f"Jako system Smart City AI (tryb MOCK) odpowiadam: {user_message.upper()}."
        return jsonify({"response": ai_response})

    try:
        #kontekts
        event_context = load_facebook_events("data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668-formatted.json")
        prompt = (
            f"Jestes doradca do wyboru wydarzenia w gdansku z pliku data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668-formatted.json "
            f"Uzytkownik mówi ci na co ma ochotę, ty musisz mu dobrać do tego wydarzenie, które jeszcze nie mineło. Jak poprosi o konkretny dzień, ma ono być w ten dzień."
            f"Twoja odpowiedź ma być krótka, tylko proponowane wydarzenie i dlaczego (max 1,2 zdania). Oto wiadomość (jeżeli jest nie na temat, odpisz: Wiadomość nie na temat): {user_message}"
            f"{event_context}"
            f"{czas}"
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        ai_response = response.text

    except Exception as e:
        ai_response = f"Błąd komunikacji z modelem AI: {e}"

    return jsonify({"response": ai_response})


@app.route('/api/chat_admin', methods=['POST'])
@login_required
def handle_chat_admin():
    class Info(BaseModel):
        Kultura_quantity: str = Field(description="Ilosc wydarzen kulturalnych:")
        Sport_quantity: str = Field(description="Ilosc wydarzen sportowych:")
        Rozrywka_quantity: str = Field(description="Ilosc wydarzen rozrywkowych:")
        Inne_quantity: str = Field(description="Ilosc innych wydarzen :")
    print("Zaczynam generowanie odpowiedzi")

    if client is None:
        ai_response = f"Jako system Smart City AI (tryb MOCK) odpowiadam: ."
        return jsonify({"response": ai_response})

    try:
        #kontekts
        event_context = load_facebook_events("data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668-formatted.json")
        prompt = (
            f"Jestes pomocnikiem przy analizie danych dla klasyfikacji  wydarzeń w gdansku z pliku data/dataset_facebook-events-scraper_2025-11-28_10-21-23-668-formatted.json "
            f"Na podstawie przesłanych danych przyporządkuj wydarzenie do jednej z czterech kategorii: KULTURA/SPORT/ROZRYWKA/INNE. Policz ile wydarzeń pasuje do kazdej kategorii. Bardzo wazne, odpowiedz samą liczbą pasujących wydarzeń według kolejności w prompcie!"
            f"{event_context}"

        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": Info.model_json_schema(),
            },

        )

        ai_response = response.text
        print(ai_response)


        print("Zakonczono operacje AL")
        with open('data.txt', 'w', encoding='utf-8') as f:
            print("Tworze plik")
            f.write(ai_response)
        # data = json.loads(ai_response)
        # with open('data.json', 'w', encoding='utf-8') as f:
        #     json.dumps(data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        ai_response = f"Błąd komunikacji z modelem AI: {e}"

    return jsonify({"response": ai_response})

if __name__ == '__main__':
    main()
