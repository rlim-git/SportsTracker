import os
import psycopg2
from datetime import datetime, timedelta
from psycopg2 import IntegrityError
from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId # <--- IMPORTANT
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
                cur.execute("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id", (username, password))
                new_user_id = cur.fetchone()[0]
                conn.commit()
                profiles_collection.insert_one({
                    "user_id": new_user_id,
                    "username": username,
                    "created_at": datetime.now(),
                    "poids": None,
                    "taille": None
                })
                cur.close()
                conn.close()
                flash("Compte créé avec succès ! Connectez-vous.", "success")
                return redirect('/login')
            except IntegrityError:
                conn.rollback()
                error = "Ce nom d'utilisateur existe déjà."
            except Exception as e:
                if conn: conn.rollback()
                error = f"Erreur technique : {e}"
            finally:
                if conn: conn.close()
    return render_template('register.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
            user_sql = cur.fetchone()
            cur.close()
            conn.close()
            if user_sql and user_sql[2] == password_input:
                session['user_id'] = user_sql[0]
                session['username'] = user_sql[1]
                return redirect('/dashboard')
            else:
                error = "Identifiants incorrects."
        except Exception as e:
            error = f"Erreur connexion base de données: {e}"
    return render_template('login.html', error=error)

# --- ROUTE CONNEXION DÉMO ---
@app.route('/demo_login')
def demo_login():
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        # On cherche l'utilisateur 'Demo' créé par init.sql
        cur.execute("SELECT id, username FROM users WHERE username = 'Demo'")
        user_demo = cur.fetchone()
        cur.close()
        conn.close()

        if user_demo:
            # Connexion automatique sans mot de passe
            session['user_id'] = user_demo[0]
            session['username'] = user_demo[1]
            flash("Bienvenue sur le compte de démonstration !", "success")
            return redirect('/dashboard')
        else:
            flash("Le compte démo n'est pas encore initialisé.", "error")
            return redirect('/')
            
    except Exception as e:
        print(f"Erreur Demo: {e}")
        flash("Impossible de se connecter au compte démo.", "error")
        return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- ROUTE : SUPPRESSION COMPTE ---
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session: return redirect('/login')

    # --- PROTECTION DU COMPTE DÉMO ---
    if session.get('username') == 'Demo':
        flash("Action interdite : Le compte de démonstration ne peut pas être supprimé.", "error")
        return redirect('/dashboard')
    # ---------------------------------

    user_id = session['user_id']
    
    try:
        # 1. Supprimer User SQL
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()

        # 2. Supprimer TOUTES les données Mongo liées (Séances + Profil)
        workouts_collection.delete_many({"user_id": user_id})
        profiles_collection.delete_many({"user_id": user_id})

        session.clear()
        flash("Votre compte et toutes vos données ont été supprimés.", "success")
        return redirect('/')
        
    except Exception as e:
        print(f"Erreur suppression compte: {e}")
        flash("Erreur lors de la suppression du compte.", "error")
        return redirect('/dashboard')

# --- ROUTE : SUPPRESSION SÉANCE ---
@app.route('/delete_session/<session_id>', methods=['POST'])
def delete_session(session_id):
    if 'user_id' not in session: return redirect('/login')
    
    try:
        # Suppression simple dans Mongo
        workouts_collection.delete_one({'_id': ObjectId(session_id)})
        flash("Séance supprimée.", "success")
    except Exception as e:
        print(f"Erreur suppression séance: {e}")
        flash("Impossible de supprimer la séance.", "error")
        
    return redirect('/dashboard')

def get_stats_for_period(start_date, end_date, user_id):
    """Calcule les statistiques d'entraînement pour une période donnée."""
    query = {
        "user_id": user_id,
        "date": {
            "$gte": start_date.strftime('%Y-%m-%d'),
            "$lte": end_date.strftime('%Y-%m-%d')
        }
    }
    workouts = list(workouts_collection.find(query))

    stats = {
        'total_sessions': len(workouts),
        'cardio_sessions': 0,
        'muscu_sessions': 0,
        'total_distance_km': 0,
        'total_duree_min': 0,
        'total_volume_kg': 0
    }

    for w in workouts:
        if w['type'] == 'Cardio':
            stats['cardio_sessions'] += 1
            stats['total_distance_km'] += w.get('details', {}).get('distance_km', 0)
            stats['total_duree_min'] += w.get('details', {}).get('duree_min', 0)
        elif w['type'] == 'Musculation':
            stats['muscu_sessions'] += 1
            if 'exercises' in w and w['exercises']: # Nouveau format
                for exo in w['exercises']:
                    stats['total_volume_kg'] += exo.get('poids', 0) * exo.get('repetitions', 0)
            elif 'details' in w: # Ancien format compatible
                stats['total_volume_kg'] += w.get('details', {}).get('poids', 0) * w.get('details', {}).get('repetitions', 0)
    
    stats['total_distance_km'] = round(stats['total_distance_km'], 1)
    stats['total_volume_kg'] = int(stats['total_volume_kg'])

    return stats

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session: return redirect('/login')
    current_user_id = session['user_id']
    current_username = session['username']

    if request.method == 'POST':
        workout_type = request.form.get('type')
        date_str = request.form.get('date')
        
        doc_to_insert = {
            "user_id": current_user_id, 
            "username": current_username, 
            "type": workout_type, 
            "date": date_str
        }

        try:
            if workout_type == 'Cardio':
                distance = float(request.form.get('distance', 0) or 0)
                duree = int(request.form.get('duree', 0) or 0)
                doc_to_insert["details"] = {'distance_km': distance, 'duree_min': duree}
            
            elif workout_type == 'Musculation':
                doc_to_insert["title"] = request.form.get('seance_title') or f"Musculation du {date_str}"
                
                exercices = request.form.getlist('exercice')
                poids_list = request.form.getlist('poids')
                reps_list = request.form.getlist('reps')
                
                exercises_data = []
                for i in range(len(exercices)):
                    if exercices[i]: # On ajoute seulement si le nom de l'exercice est renseigné
                        exercises_data.append({
                            'exercice': exercices[i],
                            'poids': float(poids_list[i] or 0),
                            'repetitions': int(reps_list[i] or 0)
                        })
                
                if not exercises_data:
                    flash("Veuillez ajouter au moins un exercice pour une séance de musculation.", "error")
                    return redirect('/dashboard')
                
                doc_to_insert["exercises"] = exercises_data
            
            workouts_collection.insert_one(doc_to_insert)
            flash("Session d'entrainement ajoutée !", "success")

        except Exception as e:
            print(f"Erreur Mongo: {e}")
            flash("Un problème est survenu lors de l'ajout de la séance.", "error")
        return redirect('/dashboard')

    # --- LOGIQUE STATS ---
    today = datetime.now()
    stats_week = get_stats_for_period(today - timedelta(days=7), today, current_user_id)
    stats_month = get_stats_for_period(today - timedelta(days=30), today, current_user_id)
    stats_3months = get_stats_for_period(today - timedelta(days=90), today, current_user_id)
    
    stats_summary = {
        'week': stats_week,
        'month': stats_month,
        'quarter': stats_3months
    }

    history = list(workouts_collection.find({"user_id": current_user_id}).sort("date", -1))
    return render_template('index.html', username=current_username, history=history, stats=stats_summary)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)