import os
import psycopg2
from flask import Flask, render_template, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    
    if request.method == 'POST':
        user_input = request.form.get('username')
        pass_input = request.form.get('password')
        
        # --- LOGIQUE DE VÉRIFICATION ---
        # Ici, on accepte tout le monde si le mot de passe est 'admin'
        # C'est suffisant pour la démo, mais on pourrait interroger Postgres ici.
        if pass_input == 'admin':
            # On pourrait stocker le user en session ici
            return redirect('/dashboard')
        else:
            error = "Identifiants invalides. Essayez mdp: 'admin'"

    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    
    if request.method == 'POST':
        # 1. Récupération des champs
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        # 2. Vérification simple
        if password != confirm:
            error = "Les mots de passe ne correspondent pas !"
        elif len(password) < 4:
            error = "Le mot de passe est trop court."
        else:
            # --- C'EST ICI QU'ON FERA L'INSERT SQL PLUS TARD ---
            # cursor.execute("INSERT INTO users ...")
            
            print(f"Nouvel utilisateur simulé : {username} / {email}")
            
            # Succès -> On redirige vers le login
            # (Idéalement on passe un message de succès, mais restons simples)
            return redirect('/login')

    return render_template('register.html', error=error)

# # Config
# PG_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
# MONGO_HOST = os.environ.get('MONGO_HOST', 'mongo')

# # Connexions
# def get_pg_connection():
#     return psycopg2.connect(
#         host=PG_HOST, database="sportdb", user="admin", password="password123"
#     )

# client = MongoClient(f'mongodb://{MONGO_HOST}:27017/')
# mongo_db = client['workout_db']
# workouts_collection = mongo_db['sessions']

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         # Sauvegarde dans MongoDB (NoSQL)
#         doc = {
#             "type": request.form.get('type'),
#             "date": request.form.get('date'),
#             "details": {} # Flexible !
#         }
        
#         # Logique dynamique selon le type
#         if request.form.get('type') == 'Cardio':
#             doc['details']['distance'] = request.form.get('distance')
#             doc['details']['duree'] = request.form.get('duree')
#         else:
#             doc['details']['exercice'] = request.form.get('exercice')
#             doc['details']['poids'] = request.form.get('poids')

#         workouts_collection.insert_one(doc)
#         return redirect('/')

#     # Lecture PostgreSQL (Relationnel)
#     conn = get_pg_connection()
#     cur = conn.cursor()
#     cur.execute("SELECT username FROM users LIMIT 1;")
#     user = cur.fetchone() # Devrait retourner 'Coach_Carter' grâce au init.sql
#     cur.close()
#     conn.close()

#     # Lecture MongoDB
#     history = list(workouts_collection.find().sort("_id", -1))

#     return render_template('index.html', username=user[0] if user else "Inconnu", history=history)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)