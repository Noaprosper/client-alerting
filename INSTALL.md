# Guide d'Installation Rapide

## Prérequis

- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Accès aux APIs Scaleway

## Installation en 5 étapes

### Étape 1: Initialiser le projet

Le projet est déjà créé dans : `/Users/cbenard/Desktop/Alert-client`

### Étape 2: Configurer la base de données

```bash
cd /Users/cbenard/Desktop/Alert-client

# Option A: Utiliser le script d'init
./init.sh

# Option B: Manuellement
createdb alert_client
psql -d alert_client -f database/schema.sql
```

### Étape 3: Importer vos organisations (CSV) 

**1. Éditez le fichier CSV avec les vrais org_ids** :

```bash
nano database/organizations.csv
```

**Format du CSV** :

```csv
org_id,name
11111111-1111-1111-1111-111111111111,Client Alpha Corp
22222222-2222-2222-2222-222222222222,Client Beta Industries
33333333-3333-3333-3333-333333333333,Client Gamma Solutions
```

**2. Importez le CSV dans la base** :

```bash
cd database
python import_csv.py organizations.csv
```

**3. Vérifiez l'import** :

```bash
psql -d alert_client -c "SELECT * FROM organizations;"
```



### Étape 4: Configurer les variables d'environnement

```bash
# Copier le fichier d'exemple
cp .env.example cron-match-incidents/.env

# Éditer les fichiers .env
nano cron-match-incidents/.env
```

**Variables requises**:

```bash
# API Scaleway (READ-ONLY!)
SCALEWAY_API_KEY=scw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# URLs des APIs
INCIDENT_API_URL=https://incresponse.incre.prd.fr-par.internal.scaleway.com/core/incidents/
CONSOLE_API_URL=https://api.scaleway.com/resource-private/v1alpha1/dashboard

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/alert_client
```



### Étape 5: Installer les dépendances

```bash
# Python (cron job)
cd cron-match-incidents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Node.js (dashboard)
cd ../dashboard
npm install
```



### Étape 6: Tester

```bash
# Tester le cron job manuellement
cd cron-match-incidents
source venv/bin/activate
python main.py

# Lancer le dashboard
cd ../dashboard
npm run dev
# Ouvrir http://localhost:3000
```



##  Configurer le cron job

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne (exécution toutes les 15 minutes)
*/15 * * * * cd /Users/cbenard/Desktop/Alert-client/cron-match-incidents && source venv/bin/activate && python main.py >> /tmp/alert-client.log 2>&1
```



## Vérification



### Base de données

```bash
psql -d alert_client -c "SELECT * FROM organizations LIMIT 5;"
psql -d alert_client -c "SELECT * FROM sync_logs ORDER BY started_at DESC LIMIT 5;"
```



### Cron job

- Vérifier les logs: `tail -f /tmp/alert-client.log`
- Vérifier les alertes: `psql -d alert_client -c "SELECT COUNT(*) FROM alerts;"`



### Dashboard

- Ouvrir [http://localhost:3000](http://localhost:3000)
- Vérifier que les cartes clients s'affichent
- Vérifier que les stats sont correctes



##  Dépannage



### Erreur de connexion à la base

```bash
# Vérifier PostgreSQL
brew services list | grep postgresql

# Redémarrer si nécessaire
brew services restart postgresql
```



### Erreur API Scaleway

- Vérifier que la clé API est valide
- Vérifier les permissions (READ-ONLY uniquement)
- Tester avec curl:

```bash
curl -H "X-Auth-Token: $SCALEWAY_API_KEY" \
  "https://api.scaleway.com/resource-private/v1alpha1/filtered-counters?organization_id=YOUR_ORG_ID&products=1&localities=1"
```



### Dashboard ne démarre pas

```bash
cd dashboard
rm -rf node_modules
npm install
npm run dev
```



##  Mettre à jour les clients

Pour ajouter/modifier les organisations:

```bash
# 1. Éditer le CSV
nano database/organizations.csv

# 2. Réimporter
cd database
python import_csv.py organizations.csv

# 3. Vérifier
psql -d alert_client -c "SELECT COUNT(*) FROM organizations;"
```



## Sécurité

### Stocker les secrets

En production, utilisez Scaleway Secret Manager:

```bash
# Créer les secrets
scw secret secret create name=alert-client-scaleway-key value=scw_xxx
scw secret secret create name=alert-client-database-url value=postgresql://...
```



## Prochaines étapes

1. ✅ Installation terminée
2. [ ] Éditer `database/organizations.csv` avec vos vrais org_ids
3. [ ] Importer le CSV: `python database/import_csv.py organizations.csv`
4. [ ] Configurer le cron job en production
5. [ ] Déployer le dashboard



