# System Metrics Agent - TP DevOps

## Membres du groupe

- MOVY IBOUNDZI Pauline Marietta
- ATALA Ferry Fertyno
- MAMEGUI IBINGA Snela Yhessi

## Presentation du projet

System Metrics Agent est une application Python modulaire qui collecte des metriques systeme et les transmet a une API FastAPI. Le TP consiste a conteneuriser l'application, orchestrer les services avec Docker Compose et publier automatiquement l'image Docker via GitHub Actions.

L'application contient deux processus :

- `api` : expose l'API FastAPI avec les routes `/health`, `/metrics` et `/metrics/latest`.
- `agent` : collecte les metriques CPU, memoire et charge systeme, puis les envoie vers l'API.

Architecture principale :

```text
system_metrics_agent/
|-- app/
|   |-- agent.py
|   |-- api.py
|   |-- collector.py
|   |-- config.py
|   |-- formatter.py
|   `-- sender.py
|-- tests/
|-- .github/workflows/ci-cd.yml
|-- Dockerfile
|-- Dockerfile.dev
|-- docker-compose.yaml
|-- docker-compose.dev.yaml
|-- docker-compose.hub.yaml
|-- .env.example
|-- requirements.prod.txt
|-- requirements-dev.txt
`-- README.md
```

## Prerequis

- Git
- Docker Desktop ou Docker Engine avec Docker Compose
- Un compte GitHub
- Un compte Docker Hub
- Un token Docker Hub cree depuis `Account Settings > Security > New Access Token`

## Configuration

Copier le fichier d'exemple puis l'adapter :

```bash
cp .env.example .env
```

Sous Windows PowerShell :

```powershell
Copy-Item .env.example .env
```

Variables utiles :

```env
METRICS_ENDPOINT=http://127.0.0.1:8000/metrics
COLLECTION_INTERVAL=5
REQUEST_TIMEOUT=5
API_PORT=8000
DOCKERHUB_USERNAME=votre-identifiant-dockerhub
IMAGE_TAG=latest
```

Le fichier `.env` ne doit jamais etre committe. En Docker Compose, l'agent utilise automatiquement `http://api:8000/metrics`, car `api` est le nom du service joignable sur le reseau Docker interne.

## Lancer en developpement

Le fichier `Dockerfile.dev` installe les dependances de developpement, inclut `pytest` et lance l'API avec le rechargement a chaud.

Construire l'image de developpement :

```bash
docker build -f Dockerfile.dev -t system-metrics-agent:dev .
```

Lancer l'API en developpement :

```bash
docker run --rm -it -p 8000:8000 --env-file .env -v "${PWD}/app:/app/app" system-metrics-agent:dev
```

Lancer les deux services en mode developpement avec Compose :

```bash
docker compose -f docker-compose.dev.yaml up --build
```

Tester l'API :

```bash
curl http://127.0.0.1:8000/health
```

Reponse attendue :

```json
{"status":"ok"}
```

## Lancer en production avec build local

Le fichier `Dockerfile` est multi-stage. Il installe seulement les dependances d'execution, utilise un utilisateur non-root et declare un healthcheck sur `/health`.

Construire l'image de production :

```bash
docker build -t system-metrics-agent:prod .
```

Lancer l'API seule :

```bash
docker run --rm -p 8000:8000 --env-file .env system-metrics-agent:prod
```

Lancer l'API et l'agent avec Docker Compose :

```bash
docker compose up --build
```

Verifier les conteneurs actifs :

```bash
docker compose ps
```

Verifier l'API :

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics/latest
```

La route `/metrics/latest` peut retourner `404` pendant quelques secondes si l'agent n'a pas encore envoye sa premiere metrique.

## Deploiement depuis Docker Hub

Apres publication par le pipeline CI/CD, renseigner l'identifiant Docker Hub dans `.env` :

```env
DOCKERHUB_USERNAME=votre-identifiant-dockerhub
IMAGE_TAG=latest
```

Recuperer l'image publiee sans utiliser le build local :

```bash
docker compose -f docker-compose.hub.yaml pull
```

Demarrer les services depuis Docker Hub :

```bash
docker compose -f docker-compose.hub.yaml up -d
```

Verifier :

```bash
docker compose -f docker-compose.hub.yaml ps
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics/latest
```

## Pipeline CI/CD

Le workflow GitHub Actions se trouve dans `.github/workflows/ci-cd.yml`.

Declenchement :

- a chaque `push` sur `main` ou `master` ;
- a chaque `pull_request` vers `main` ou `master`.

Etapes du pipeline :

1. Recuperation du code du depot.
2. Build de l'image Docker de production avec le `Dockerfile`.
3. Installation des dependances de test.
4. Execution de `pytest -q`.
5. Connexion a Docker Hub uniquement lors d'un `push`.
6. Publication de l'image Docker si les tests passent.

Tags publies :

- `latest`
- le SHA du commit GitHub

Secrets GitHub requis dans `Settings > Secrets and variables > Actions` :

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

Ces identifiants ne doivent jamais etre ecrits en clair dans le code, le README, l'image Docker ou l'historique Git.

## Images Docker Hub

Lien du depot Docker Hub a completer apres publication :

```text
https://hub.docker.com/r/votre-identifiant-dockerhub/system-metrics-agent
```

Exemple d'image attendue :

```text
votre-identifiant-dockerhub/system-metrics-agent:latest
votre-identifiant-dockerhub/system-metrics-agent:<sha-du-commit>
```

## Tests

Executer les tests localement :

```bash
pip install -r requirements-dev.txt
pytest -q
```

Executer les tests dans l'image de developpement :

```bash
docker build -f Dockerfile.dev -t system-metrics-agent:dev .
docker run --rm system-metrics-agent:dev pytest -q
```

## Choix techniques

- Une seule image de production est utilisee pour les deux processus. Le service `api` conserve la commande par defaut `uvicorn`, tandis que le service `agent` surcharge la commande avec `python -m app.agent`.
- Le `Dockerfile` est multi-stage pour separer l'installation des dependances de l'image finale.
- L'image de production utilise `requirements.prod.txt`, sans `pytest`, afin de reduire la surface et la taille de l'image.
- Les conteneurs s'executent avec un utilisateur non-root.
- Docker Compose cree un reseau dedie `metrics-network`, ce qui permet a l'agent de contacter l'API avec `http://api:8000/metrics`.
- Le fichier `docker-compose.hub.yaml` permet de demontrer un deploiement depuis Docker Hub sans build local.

## Difficultes rencontrees

- Le projet source annoncait une suite de tests, mais le dossier `tests` n'etait pas present dans le depot recupere. Une suite de tests minimale a donc ete ajoutee pour valider l'API, le formatage et l'envoi HTTP.
- L'agent ne doit pas appeler `127.0.0.1` entre conteneurs, car cette adresse pointerait vers son propre conteneur. La configuration Compose force donc `METRICS_ENDPOINT=http://api:8000/metrics`.
- La production ne doit pas embarquer les dependances de test. Les dependances ont donc ete separees entre `requirements.prod.txt` et `requirements-dev.txt`.

## Preuves de fonctionnement

Ajouter ici les captures d'ecran ou extraits de logs demandes lors du rendu :

- Pipeline GitHub Actions vert.
- Image publiee sur Docker Hub.
- Resultat de `docker compose ps`.
- Resultat de `curl http://127.0.0.1:8000/health`.
- Resultat de `curl http://127.0.0.1:8000/metrics/latest`.

Exemple de logs attendus :

```text
api-1    | Uvicorn running on http://0.0.0.0:8000
agent-1  | Metriques envoyees avec succes. HTTP=201
```

## Nettoyage

Arreter les services :

```bash
docker compose down
```

Supprimer les conteneurs et reseaux du deploiement Docker Hub :

```bash
docker compose -f docker-compose.hub.yaml down
```
