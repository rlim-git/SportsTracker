import os
import psycopg2
from flask import Flask, render_template, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

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