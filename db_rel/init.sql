-- 1. Nettoyage
-- DROP TABLE IF EXISTS sessions;
-- DROP TABLE IF EXISTS users;

-- 2. Création de la table USERS
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Création de la table SESSIONS (Mise à jour avec détails)
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- 'Cardio' ou 'Musculation'
    date DATE NOT NULL,
    
    -- Détails Musculation (Seront NULL si type = Cardio)
    exercice VARCHAR(100),
    poids FLOAT,
    repetitions INTEGER,

    -- Détails Cardio (Seront NULL si type = Musculation)
    distance_km FLOAT,
    duree_min INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Création de l'ADMIN
INSERT INTO users (username, password)
VALUES ('admin', 'admin')
ON CONFLICT (username) DO NOTHING;

-- 5. Insertion des SÉANCES DE TEST

-- Séance 1 : Cardio (On remplit distance/duree, on laisse vide poids/reps)
INSERT INTO sessions (user_id, type, date, distance_km, duree_min)
VALUES (1, 'Cardio', CURRENT_DATE, 10.5, 60);

-- Séance 2 : Musculation (On remplit exercice/poids/reps, on laisse vide distance/duree)
INSERT INTO sessions (user_id, type, date, exercice, poids, repetitions)
VALUES (1, 'Musculation', CURRENT_DATE, 'Bench Press', 80, 10);