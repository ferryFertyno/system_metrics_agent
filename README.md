# System Metrics Agent - TP DevOps

## Membres du groupe

- MOVY IBOUNDZI Pauline Marietta
- ATALA Ferry Fertyno
- MAMEGUI IBINGA Snela Yhessi

---

## 1. Présentation du projet

**System Metrics Agent** est une application Python modulaire permettant de collecter des métriques système et de les transmettre à une API FastAPI.

L'objectif du TP est de :

- conteneuriser l'application avec Docker ;
- orchestrer les services avec Docker Compose ;
- disposer d'une image de production et d'une image de développement ;
- exécuter les tests automatisés ;
- mettre en place une intégration continue avec GitHub Actions ;
- publier les images Docker sur Docker Hub.

L'application comporte deux processus principaux :

- **API** : expose une API FastAPI permettant de recevoir et consulter les métriques ;
- **Agent** : collecte les métriques système puis les transmet à l'API.

---

## 2. Architecture du projet

```text
system_metrics_agent/
│
├── app/
│   ├── agent.py
│   ├── api.py
│   ├── collector.py
│   ├── config.py
│   ├── formatter.py
│   └── sender.py
│
├── tests/
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml
│
├── Dockerfile
├── Dockerfile.dev
├── docker-compose.yaml
├── docker-compose.dev.yaml
├── docker-compose.hub.yaml
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
├── requirements.prod.txt
├── requirements-dev.txt
└── README.md
```

Architecture Docker :

```text
                    Docker Compose
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
         metrics-api          metrics-agent
              │                     │
         FastAPI :8000              │
              │                     │
              └───────◄─────────────┘
                  /metrics
```

---

## 3. Prérequis

Le projet nécessite :

- Git ;
- Docker Desktop ;
- Docker Compose ;
- un compte GitHub ;
- un compte Docker Hub.

L'installation de Docker a été vérifiée avec :

```powershell
docker run hello-world
```

Le résultat `Hello from Docker!` confirme que Docker fonctionne correctement.

---

## 4. Configuration

Copier le fichier `.env.example` vers `.env`.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Exemple de variables utilisées :

```env
METRICS_ENDPOINT=http://127.0.0.1:8000/metrics
COLLECTION_INTERVAL=5
REQUEST_TIMEOUT=5
API_PORT=8000
DOCKERHUB_USERNAME=fertyno
IMAGE_TAG=latest
```

### Important

Le fichier `.env` contient la configuration locale et ne doit jamais être envoyé sur GitHub.

En environnement Docker Compose, l'agent communique avec l'API grâce au nom du service Docker :

```text
http://api:8000/metrics
```

et non :

```text
http://127.0.0.1:8000/metrics
```

Dans un conteneur, `127.0.0.1` désigne le conteneur lui-même.

---

# 5. Dockerfile de production

Le fichier `Dockerfile` permet de construire l'image de production.

L'image utilise une approche multi-stage afin de séparer l'installation des dépendances de l'image finale.

L'image de production :

- utilise Python 3.12 slim ;
- installe les dépendances nécessaires à l'exécution ;
- n'embarque pas les dépendances de développement ;
- utilise un utilisateur non-root ;
- expose l'API FastAPI ;
- dispose d'un healthcheck.

### Construire l'image de production

```powershell
docker build -t system-metrics-agent:latest .
```

Vérifier les images :

```powershell
docker images
```

Image produite :

```text
system-metrics-agent:latest
```

---

# 6. Image de développement

Le fichier `Dockerfile.dev` est destiné au développement et aux tests.

Il permet notamment d'installer les dépendances nécessaires à `pytest`.

### Construire l'image de développement

```powershell
docker build -f Dockerfile.dev -t system-metrics-agent:dev .
```

Vérifier les images :

```powershell
docker images
```

Image de développement :

```text
system-metrics-agent:dev
```

---

# 7. Docker Compose

Le fichier `docker-compose.yaml` permet d'orchestrer deux services :

```text
api
agent
```

Le service `api` expose le port `8000` sur la machine hôte.

Le service `agent` communique avec l'API grâce au réseau Docker interne.

### Lancement avec Docker Compose

```powershell
docker compose up --build -d
```

### Vérifier les conteneurs

```powershell
docker compose ps
```

Résultat obtenu lors de la validation :

```text
NAME            IMAGE                         SERVICE   STATUS
metrics-agent   system-metrics-agent:latest   agent     Up (healthy)
metrics-api     system-metrics-agent:latest   api       Up (healthy)
```

Le service API est accessible depuis la machine hôte avec :

```text
http://localhost:8000
```

---

# 8. Résolution du conflit de conteneur

Lors du premier lancement de Docker Compose, un conflit est apparu car un conteneur nommé `metrics-api` existait déjà.

Erreur rencontrée :

```text
Conflict. The container name "/metrics-api" is already in use
```

Le problème a été résolu avec :

```powershell
docker compose down --remove-orphans
docker rm -f metrics-api
docker compose up --build -d
```

Après cette opération, les deux conteneurs ont démarré correctement et sont devenus `healthy`.

---

# 9. Vérification de l'API

L'API est accessible à :

```text
http://localhost:8000
```

La documentation interactive Swagger est disponible à :

```text
http://localhost:8000/docs
```

La documentation Swagger affiche les routes suivantes :

```text
GET  /metrics
POST /metrics
GET  /health
GET  /metrics/latest
```

---

# 10. Endpoint Health

L'endpoint permettant de vérifier l'état de l'API est :

```text
GET /health
```

Test :

```powershell
curl http://127.0.0.1:8000/health
```

Réponse attendue :

```json
{
  "status": "ok"
}
```

---

# 11. Endpoint Metrics

Pour consulter les métriques :

```text
GET /metrics
```

Pour envoyer des métriques :

```text
POST /metrics
```

Pour récupérer les dernières métriques :

```text
GET /metrics/latest
```

Test :

```powershell
curl http://127.0.0.1:8000/metrics/latest
```

La route `/metrics/latest` peut retourner temporairement `404` au démarrage si l'agent n'a pas encore envoyé sa première métrique.

---

# 12. Développement

Pour construire l'image de développement :

```powershell
docker build -f Dockerfile.dev -t system-metrics-agent:dev .
```

Pour lancer l'environnement de développement avec Docker Compose :

```powershell
docker compose -f docker-compose.dev.yaml up --build
```

Pour exécuter les tests dans l'image de développement :

```powershell
docker run --rm system-metrics-agent:dev pytest -q
```

---

# 13. Tests

Les tests sont placés dans :

```text
tests/
```

Les dépendances de développement sont définies dans :

```text
requirements-dev.txt
```

Installation :

```powershell
pip install -r requirements-dev.txt
```

Exécution :

```powershell
pytest -q
```

Les tests peuvent également être exécutés dans l'image Docker de développement :

```powershell
docker build -f Dockerfile.dev -t system-metrics-agent:dev .
docker run --rm system-metrics-agent:dev pytest -q
```

---

# 14. Docker Hub

Le compte Docker Hub utilisé pour le projet est :

```text
fertyno
```

Le dépôt Docker Hub du projet est :

```text
https://hub.docker.com/r/fertyno/system-metrics-agent
```

Les images prévues sont :

```text
fertyno/system-metrics-agent:latest
fertyno/system-metrics-agent:dev
```

Le tag `latest` correspond à l'image de production.

Le tag `dev` correspond à l'image construite avec `Dockerfile.dev`.

## Publication de l'image de production

Connexion :

```powershell
docker login
```

Tag :

```powershell
docker tag system-metrics-agent:latest fertyno/system-metrics-agent:latest
```

Publication :

```powershell
docker push fertyno/system-metrics-agent:latest
```

## Publication de l'image de développement

Construction :

```powershell
docker build -f Dockerfile.dev -t system-metrics-agent:dev .
```

Tag :

```powershell
docker tag system-metrics-agent:dev fertyno/system-metrics-agent:dev
```

Publication :

```powershell
docker push fertyno/system-metrics-agent:dev
```

---

# 15. Git et GitHub

Le projet est versionné avec Git.

Vérifier l'état du dépôt :

```powershell
git status
```

Ajouter les fichiers du projet :

```powershell
git add .env.example .gitignore README.md .dockerignore Dockerfile Dockerfile.dev docker-compose.yaml .github tests
```

Créer un commit :

```powershell
git commit -m "Mise à jour de la documentation Docker et CI/CD"
```

Envoyer les modifications :

```powershell
git push origin main
```

Le fichier `.env` ne doit jamais être ajouté au dépôt Git.

---

# 16. Pipeline CI/CD

Le workflow GitHub Actions se trouve dans :

```text
.github/workflows/ci-cd.yml
```

Le pipeline a pour objectif d'automatiser :

1. la récupération du code ;
2. la construction de l'image Docker ;
3. l'installation des dépendances de test ;
4. l'exécution de `pytest` ;
5. la connexion à Docker Hub ;
6. la publication de l'image Docker.

Le workflow est déclenché selon les événements définis dans le fichier :

```text
.github/workflows/ci-cd.yml
```

---

# 17. Secrets GitHub

Les identifiants Docker Hub ne doivent pas être écrits directement dans le code.

Les secrets doivent être configurés dans :

```text
GitHub
→ Settings
→ Secrets and variables
→ Actions
```

Secrets nécessaires :

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
```

Le nom d'utilisateur Docker Hub utilisé est :

```text
fertyno
```

Le token Docker Hub doit rester confidentiel.

Il ne doit jamais être :

- écrit dans le code ;
- ajouté au README ;
- ajouté dans `.env` versionné ;
- publié dans une image Docker ;
- envoyé dans l'historique Git.

---

# 18. Déploiement depuis Docker Hub

Le fichier :

```text
docker-compose.hub.yaml
```

permet de démarrer les services en utilisant les images publiées sur Docker Hub au lieu de reconstruire les images localement.

Récupérer les images :

```powershell
docker compose -f docker-compose.hub.yaml pull
```

Démarrer les services :

```powershell
docker compose -f docker-compose.hub.yaml up -d
```

Vérifier :

```powershell
docker compose -f docker-compose.hub.yaml ps
```

Tester l'API :

```powershell
curl http://127.0.0.1:8000/health
```

Puis :

```powershell
curl http://127.0.0.1:8000/metrics/latest
```

---

# 19. Preuves de fonctionnement

Les éléments suivants peuvent être ajoutés au rendu du TP.

## Vérification de Docker

Commande :

```powershell
docker run hello-world
```

Résultat obtenu :

```text
Hello from Docker!

This message shows that your installation appears to be working correctly.
```

## Vérification des conteneurs

Commande :

```powershell
docker compose ps
```

Résultat obtenu :

```text
NAME            IMAGE                         SERVICE   STATUS
metrics-agent   system-metrics-agent:latest   agent     Up (healthy)
metrics-api     system-metrics-agent:latest   api       Up (healthy)
```

## Documentation Swagger

URL :

```text
http://localhost:8000/docs
```

Endpoints visibles :

```text
GET  /metrics
POST /metrics
GET  /health
GET  /metrics/latest
```

## Image Docker Hub

Dépôt :

```text
https://hub.docker.com/r/fertyno/system-metrics-agent
```

Images :

```text
fertyno/system-metrics-agent:latest
fertyno/system-metrics-agent:dev
```

## Pipeline GitHub Actions

Une capture du workflow GitHub Actions pourra être ajoutée au rendu après validation du pipeline.

---

# 20. Difficultés rencontrées

## Conflit de nom de conteneur

Lors du premier lancement de Docker Compose, le conteneur `metrics-api` existait déjà.

Docker a retourné :

```text
Conflict. The container name "/metrics-api" is already in use
```

Le conteneur existant a été supprimé puis Docker Compose a été relancé.

## Communication entre les conteneurs

L'agent ne doit pas utiliser :

```text
127.0.0.1
```

pour contacter l'API depuis Docker.

Dans Docker Compose, l'agent utilise :

```text
http://api:8000/metrics
```

car `api` correspond au nom du service Docker.

## Séparation production / développement

Deux Dockerfiles sont utilisés :

```text
Dockerfile
```

pour la production :

```text
system-metrics-agent:latest
```

et :

```text
Dockerfile.dev
```

pour le développement et les tests :

```text
system-metrics-agent:dev
```

Cette séparation permet de ne pas inclure inutilement les dépendances de développement dans l'image de production.

---

# 21. Choix techniques

Les principaux choix techniques réalisés sont :

- utilisation de Docker pour conteneuriser l'application ;
- utilisation de Docker Compose pour orchestrer l'API et l'agent ;
- utilisation de Python 3.12 slim ;
- utilisation d'un Dockerfile multi-stage ;
- utilisation d'un utilisateur non-root ;
- séparation des dépendances de production et de développement ;
- utilisation d'un healthcheck ;
- communication entre les services via le réseau Docker ;
- utilisation de GitHub Actions pour l'automatisation ;
- publication des images sur Docker Hub.

---

# 22. État du projet

Les éléments suivants ont été validés localement :

```text
Docker installé                         OK
docker run hello-world                  OK
Dockerfile                              OK
Dockerfile.dev                          OK
docker-compose.yaml                     OK
Construction de l'image                 OK
Conteneur metrics-api                   OK
Conteneur metrics-agent                 OK
Healthcheck                             OK
API FastAPI                             OK
Swagger /docs                           OK
GET /health                             OK
GET /metrics                             OK
POST /metrics                            OK
GET /metrics/latest                     OK
Compte Docker Hub fertyno               OK
Dépôt Docker Hub                        OK
```

La publication finale des images Docker Hub et la validation finale du pipeline GitHub Actions doivent être confirmées après leur exécution.

---

# 23. Nettoyage

Pour arrêter les services locaux :

```powershell
docker compose down
```

Pour arrêter le déploiement utilisant Docker Hub :

```powershell
docker compose -f docker-compose.hub.yaml down
```

---

# 24. Lien Docker Hub

```text
https://hub.docker.com/r/fertyno/system-metrics-agent
```
