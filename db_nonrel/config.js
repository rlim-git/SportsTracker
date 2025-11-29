// db_nonrel/config.js
db = db.getSiblingDB('workout_db');

// Création des collections
try { db.createCollection('sessions'); } catch (e) { print("Collection 'sessions' existe déjà"); }

// 2. Séance CARDIO (Reste inchangée, utilise toujours 'details')
db.sessions.updateOne(
    { user_id: 1, type: "Cardio", info: "init_test" },
    {
        $setOnInsert: {
            user_id: 1,
            username: "admin",
            type: "Cardio",
            date: new Date().toISOString().split('T')[0],
            details: {
                distance_km: 10.5,
                duree_min: 60
            }
        }
    },
    { upsert: true }
);

// 3. Séance MUSCULATION (Mise à jour : Tableau 'exercises')
db.sessions.updateOne(
    { user_id: 1, type: "Musculation", info: "init_test" },
    {
        $setOnInsert: {
            user_id: 1,
            username: "admin",
            type: "Musculation",
            date: new Date().toISOString().split('T')[0],
            
            // NOUVEAU FORMAT : Titre + Liste d'exercices
            title: "Séance Full Body (Démo)",
            exercises: [
                {
                    exercice: "Bench Press",
                    poids: 80,
                    repetitions: 10
                },
                {
                    exercice: "Squat",
                    poids: 100,
                    repetitions: 8
                }
            ]
        }
    },
    { upsert: true }
);

print("--- Initialisation MongoDB terminée : Admin, Cardio et Muscu créés ---");