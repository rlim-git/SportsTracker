import os
import psycopg2
from datetime import datetime
from psycopg2 import IntegrityError
from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient
from urllib.parse import quote_plus

app = Flask(__name__)
app.secret_key = 'cle_super_secure'

# --- CONFIGURATION BDD ---
PG_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
PG_DB = os.environ.get('POSTGRES_DB', 'sportdb')
PG_USER = os.environ.get('POSTGRES_USER', 'admin')
PG_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'password')

MONGO_HOST = os.environ.get('MONGO_HOST', 'mongo')
MONGO_USER = os.environ.get('MONGO_USER', 'root')
MONGO_PASS = os.environ.get('MONGO_PASS', 'password')

# --- FILTRE DATE ---
@app.template_filter('date_fr')
def date_fr(value):
    if not value: return ""
    mois = {'01': 'Janvier', '02': 'Février', '03': 'Mars', '04': 'Avril', '05': 'Mai', '06': 'Juin', '07': 'Juillet', '08': 'Août', '09': 'Septembre', '10': 'Octobre', '11': 'Novembre', '12': 'Décembre'}
    try:
        if isinstance(value, str):
            parts = value.split('-')
            if len(parts) == 3: return f"{parts[2]} {mois.get(parts[1], parts[1])} {parts[0]}"
        elif isinstance(value, datetime):
            return f"{value.day} {mois.get(f'{value.month:02}', str(value.month))} {value.year}"
    except: return value
    return value

# --- CONNEXIONS ---
def get_pg_connection():
    return psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASSWORD)

uri = "mongodb://%s:%s@%s:27017/" % (quote_plus(MONGO_USER), quote_plus(MONGO_PASS), MONGO_HOST)
try:
    client = MongoClient(uri)
    mongo_db = client['workout_db']
    workouts_collection = mongo_db['sessions']
    profiles_collection = mongo_db['users_profile']
except Exception as e:
    print(f"Erreur connexion Mongo: {e}")

# ================= ROUTES =================
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            error = "Les mots de passe ne correspondent pas."
        else:
            conn = get_pg_connection()
            cur = conn.cursor()
            try:
                # 1. SQL (Maître)
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id", (username, password))
                new_user_id = cur.fetchone()[0]
                conn.commit()
                
                # 2. Mongo (Esclave + Auth possible)
                profiles_collection.insert_one({
                    "user_id": new_user_id,
                    "username": username,
                    "password": password,
                    "created_at": datetime.now(),
                    "poids": None,
                    "taille": None
                })
                cur.close()
                conn.close()
                return redirect('/login')
            except IntegrityError:
                conn.rollback()
                error = "Ce nom d'utilisateur existe déjà."
            except Exception as e:
                if conn: conn.rollback()
                error = f"Erreur : {e}"
            finally:
                if conn: conn.close()
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']
        db_source = request.form.get('db_source', 'postgres') # 'postgres' ou 'mongo'

        user_found = None
        
        # --- CAS 1 : Connexion via POSTGRES ---
        if db_source == 'postgres':
            try:
                conn = get_pg_connection()
                cur = conn.cursor()
                cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
                user_sql = cur.fetchone()
                cur.close()
                conn.close()
                
                if user_sql and user_sql[2] == password_input:
                    user_found = {'id': user_sql[0], 'username': user_sql[1]}
            except Exception as e:
                error = f"Erreur SQL: {e}"

        # --- CAS 2 : Connexion via MONGO ---
        elif db_source == 'mongo':
            try:
                # On cherche l'utilisateur dans la collection profiles
                user_mongo = profiles_collection.find_one({"username": username})
                
                if user_mongo and user_mongo.get('password') == password_input:
                    user_found = {'id': user_mongo['user_id'], 'username': user_mongo['username']}
                elif user_mongo and 'password' not in user_mongo:
                    error = "Ce compte ancien n'a pas de mot de passe Mongo. Utilisez Postgres."
            except Exception as e:
                error = f"Erreur Mongo: {e}"

        # --- VERDICT ---
        if user_found:
            session['user_id'] = user_found['id']
            session['username'] = user_found['username']
            session['source'] = db_source
            return redirect('/dashboard')
        else:
            if not error: error = f"Identifiants incorrects (via {db_source})."

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session: return redirect('/login')
    current_user_id = session['user_id']
    current_username = session['username']

    if request.method == 'POST':
        workout_type = request.form.get('type')
        date_str = request.form.get('date')
        conn = get_pg_connection()
        cur = conn.cursor()
        try:
            exercice, poids, reps, distance, duree = None, None, None, None, None
            doc_details = {}

            if workout_type == 'Cardio':
                distance = float(request.form.get('distance', 0) or 0)
                duree = int(request.form.get('duree', 0) or 0)
                cur.execute("INSERT INTO sessions (user_id, type, date, distance_km, duree_min) VALUES (%s, %s, %s, %s, %s)", 
                           (current_user_id, workout_type, date_str, distance, duree))
                doc_details = {'distance_km': distance, 'duree_min': duree}
            elif workout_type == 'Musculation':
                exercice = request.form.get('exercice')
                poids = float(request.form.get('poids', 0) or 0)
                reps = int(request.form.get('reps', 0) or 0)
                cur.execute("INSERT INTO sessions (user_id, type, date, exercice, poids, repetitions) VALUES (%s, %s, %s, %s, %s, %s)", 
                           (current_user_id, workout_type, date_str, exercice, poids, reps))
                doc_details = {'exercice': exercice, 'poids': poids, 'repetitions': reps}
            
            conn.commit()
            workouts_collection.insert_one({
                "user_id": current_user_id, "username": current_username, "type": workout_type, "date": date_str, "details": doc_details
            })
            
            # --- SUCCES ---
            flash("Session d'entrainement ajouté !", "success")

        except Exception as e:
            conn.rollback()
            print(f"Erreur: {e}")
            # --- ERREUR ---
            flash("Affiche problème", "error")
        finally:
            cur.close()
            conn.close()
        return redirect('/dashboard')

    history = list(workouts_collection.find({"user_id": current_user_id}).sort("date", -1))
    return render_template('index.html', username=current_username, history=history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)