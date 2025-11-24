import os
import psycopg2
from psycopg2 import IntegrityError # Pour gérer les erreurs "Utilisateur existe déjà"
from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from urllib.parse import quote_plus

app = Flask(__name__)
# --- SÉCURITÉ (Sessions) ---
# Clé secrète requise pour utiliser session[...]
app.secret_key = 'cle_super_secure'

# --- CONFIGURATION BDD ---
PG_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
PG_DB = os.environ.get('POSTGRES_DB', 'sportdb')
PG_USER = os.environ.get('POSTGRES_USER', 'admin')
PG_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'password')

MONGO_HOST = os.environ.get('MONGO_HOST', 'mongo')
MONGO_USER = os.environ.get('MONGO_USER', 'root')
MONGO_PASS = os.environ.get('MONGO_PASS', 'password')

# --- FONCTION DE CONNEXION SQL ---
def get_pg_connection():
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )
    return conn

# --- CONNEXION MONGO (Globale) ---
uri = "mongodb://%s:%s@%s:27017/" % (
    quote_plus(MONGO_USER), 
    quote_plus(MONGO_PASS), 
    MONGO_HOST
)
try:
    client = MongoClient(uri)
    mongo_db = client['workout_db']
    workouts_collection = mongo_db['sessions']
except Exception as e:
    print(f"Erreur connexion Mongo: {e}")


# ================= ROUTES =================

@app.route('/')
def home():
    # Page de présentation
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
                # INSERTION SQL
                # ATTENTION : En production, on hashe le mot de passe (bcrypt) !
                # Pour le projet école, on stocke en clair comme demandé pour l'instant.
                cur.execute(
                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                    (username, password)
                )
                conn.commit() # Valider l'enregistrement
                cur.close()
                conn.close()
                return redirect('/login') # Succès -> on va au login
            except IntegrityError:
                conn.rollback() # Annuler la transaction en erreur
                error = "Ce nom d'utilisateur existe déjà."
            except Exception as e:
                conn.rollback()
                error = f"Erreur base de données : {e}"
            finally:
                if conn: conn.close()

    return render_template('register.html', error=error)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        conn = get_pg_connection()
        cur = conn.cursor()
        
        # REQUÊTE SQL : On cherche l'utilisateur par son pseudo
        cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cur.fetchone() # Renvoie un tuple (id, username, password) ou None
        
        cur.close()
        conn.close()

        if user:
            # user[2] correspond à la colonne password
            if user[2] == password_input:
                # SUCCÈS : On ouvre la session
                session['user_id'] = user[0]
                session['username'] = user[1]
                return redirect('/dashboard')
            else:
                error = "Mot de passe incorrect."
        else:
            error = "Utilisateur inconnu."

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear() # On vide la session
    return redirect('/')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # VÉRIFICATION DE SÉCURITÉ
    if 'user_id' not in session:
        return redirect('/login')

    current_user_id = session['user_id']
    current_username = session['username']

    # 1. GESTION DU FORMULAIRE (POST)
    if request.method == 'POST':
        workout_type = request.form.get('type')
        date = request.form.get('date')
        
        # Création du document pour MongoDB
        doc = {
            "user_id": current_user_id, # Lien avec SQL !
            "username": current_username, # Pour l'affichage facile
            "type": workout_type,
            "date": date,
            "details": {}
        }
        
        if workout_type == 'Cardio':
            doc['details']['distance'] = request.form.get('distance')
            doc['details']['duree'] = request.form.get('duree')
        elif workout_type == 'Musculation':
            doc['details']['exercice'] = request.form.get('exercice')
            doc['details']['poids'] = request.form.get('poids')
            doc['details']['reps'] = request.form.get('reps')

        # INSERTION MONGO
        workouts_collection.insert_one(doc)
        return redirect('/dashboard')

    # 2. AFFICHAGE (GET) - Récupération depuis MongoDB
    # On filtre pour ne voir que SES propres séances ou toutes (au choix)
    # Ici, on affiche tout pour la démo, ou filtre par {"user_id": current_user_id}
    history = list(workouts_collection.find({"user_id": current_user_id}).sort("_id", -1))

    return render_template('index.html', username=current_username, history=history)


if __name__ == '__main__':
    # Le host='0.0.0.0' est important pour Docker
    app.run(host='0.0.0.0', port=5000, debug=True)