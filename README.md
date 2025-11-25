# 🏋️ SportTracker : Votre Carnet d'Entraînement Numérique
Groupe :
- Remy LIM
- Jugurtha MENASRIA

## 🎯 Objectif du Projet

**SportTracker** est un carnet d'entraînement numérique destiné aux pratiquants de **CrossFit** et de **Musculation**. Il vise à offrir une plateforme centralisée pour **suivre les performances**, **enregistrer les séances** (WODs, séries, répétitions, poids), et **visualiser la progression** au fil du temps.

---

## 🛠️ Stack Technique et Architecture

Ce projet utilise une architecture conteneurisée (micro-services) pour garantir la portabilité, la scalabilité et la facilité de déploiement en environnement de développement.

| Composant | Rôle | Technologie |
| :--- | :--- | :--- |
| **Serveur Web** | Logique métier de l'application et API. | Flask (Micro-Framework Python) |
| **DB Relationnelle** | Gestion des données structurées et critiques (Utilisateurs, **Performances**, Records). | **PostgreSQL** |
| **DB Non-Relationnelle** | Gestion des données flexibles (Logs d'activité bruts, Notifications, Statistiques agrégées en cache). | **MongoDB** |
| **Orchestration** | Définition et gestion de l'environnement multi-conteneurs. | **Docker Compose** |

### 📂 Structure du Répertoire (Phase Initiale)
```text
SportTracker/
├── src/
│   ├── templates/           # Code source de l'application
|   |   └── Fichiers HTML
|   ├── static/css/         # Fichiers CSS
│   ├── Dockerfile           # Build l'image du serveur web
│   └── requirements.txt     # Dépendances
├── data/
│   ├── postgres/            # Volume persistant pour PostgreSQL
│   └── mongo/               # Volume persistant pour MongoDB
├── db_rel/
│   └── init.sql             # Script d'initialisation de la DB relationnelle
├── db_nonrel/
│   └── config.js            # Fichier de configuration MongoDB
├── nginx.conf               # Configuration du Reverse Proxy
├── README.md
└── docker-compose.yml       # Orchestration des services
```

## Définition de l'environnement

---

## 🚀 Démarrage Rapide (Environnement de Développement)

L'environnement complet de l'application est géré par Docker Compose.

### Prérequis

Assurez-vous d'avoir installé sur votre machine :
1.  **Docker Engine**
2.  **Docker Compose**

### Lancement de l'environnement

1.  Placez-vous à la racine du projet (`SportTracker/`).

2.  Lancez tous les services (Web, PostgreSQL, MongoDB) :
```bash
docker compose up --build -d
```

3.  Vérifiez que les trois conteneurs sont en cours d'exécution :

```bash
docker ps
 ```

*Votre application Web devrait être accessible à l'adresse suivante :* `http://localhost:80`

### Arrêt de l'environnement

Pour arrêter et supprimer les conteneurs (mais conserver les volumes de données) :

```bash
docker compose down
```

### Pour supprimer les conteneurs et les volumes de données persistants :

```Bash
docker compose down -v
```