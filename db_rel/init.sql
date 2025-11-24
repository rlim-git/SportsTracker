-- 1. On nettoie si besoin (Optionnel, mais pratique en dev)
-- DROP TABLE IF EXISTS users;

-- 2. Création de la table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Insertion d'un utilisateur de test (Admin)
-- Le mot de passe est ici "admin"
INSERT INTO users (username, password) 
VALUES 
    ('admin', 'admin'),
    ('sportif', '1234')
ON CONFLICT (username) DO NOTHING; 
-- "ON CONFLICT DO NOTHING" évite que le script plante si l'admin existe déjà