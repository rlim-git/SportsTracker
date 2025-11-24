// db_nonrel/config.js

// 1. On bascule sur la base de données définie dans app.py
db = db.getSiblingDB('workout_db');

// 2. On crée explicitement la collection 'sessions'
db.createCollection('sessions');

print("--- Initialisation MongoDB terminée : DB 'workout_db' créée ---");