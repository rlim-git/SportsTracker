-- 1. Nettoyage
-- DROP TABLE IF EXISTS users;

-- 2. Création de la table USERS
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Création de l'ADMIN
INSERT INTO users (username, password)
VALUES ('admin', 'admin')
ON CONFLICT (username) DO NOTHING;