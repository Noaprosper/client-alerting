# ⚡ Quick Start - Alert Client Dashboard

## 🎯 En 5 minutes

### 1️⃣ Initialiser la base de données

```bash
cd /Users/cbenard/Desktop/Alert-client
./init.sh
```

### 2️⃣ Ajouter vos organisations

**Méthode simple** : Éditer le fichier CSV

```bash
nano database/organizations.csv
```

Remplacer par vos vrais org_ids Scaleway :

```csv
org_id,name
11111111-1111-1111-1111-111111111111,Mon Premier Client
22222222-2222-2222-2222-222222222222,Mon Deuxième Client
33333333-3333-3333-3333-333333333333,Mon Troisième Client
```

**Importer dans la base** :

```bash
python database/import_csv.py organizations.csv
```

### 3️⃣ Configurer les APIs

```bash
# Copier le fichier d'exemple
cp .env.example cron-match-incidents/.env

# Éditer avec vos tokens
nano cron-match-incidents/.env
```

Ajouter vos valeurs :

```bash
# Token Scaleway (READ-ONLY uniquement !)
SCALEWAY_API_KEY=scw_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# URLs (normalement pas besoin de changer)
INCIDENT_API_URL=https://incresponse.incre.prd.fr-par.internal.scaleway.com/core/incidents/
CONSOLE_API_URL=https://api.scaleway.com/resource-private/v1alpha1/dashboard

# Base de données
DATABASE_URL=postgresql://localhost:5432/alert_client
```

### 4️⃣ Tester le cron job

```bash
cd cron-match-incidents
source venv/bin/activate
python main.py
```

Vous devriez voir :
```
✅ Connected to database
✅ Fetched X open incidents
✅ Found X organizations
✅ Completed successfully
```

### 5️⃣ Lancer le dashboard

```bash
cd ../dashboard
npm install
npm run dev
```

Ouvrir **http://localhost:3000** 🎉

---

## 📅 Automatiser (cron)

```bash
crontab -e
```

Ajouter cette ligne (exécution toutes les 15 min) :

```bash
*/15 * * * * cd /Users/cbenard/Desktop/Alert-client/cron-match-incidents && source venv/bin/activate && python main.py >> /tmp/alert-client.log 2>&1
```

---

## 🔧 Commandes utiles

### Vérifier les organisations
```bash
psql -d alert_client -c "SELECT org_id, name FROM organizations;"
```

### Voir les alertes
```bash
psql -d alert_client -c "SELECT COUNT(*) FROM alerts WHERE status='active';"
```

### Logs du cron
```bash
tail -f /tmp/alert-client.log
```

### Réimporter le CSV
```bash
cd database
python import_csv.py organizations.csv
```

---

## ✅ Checklist

- [ ] Base de données initialisée (`./init.sh`)
- [ ] Fichier CSV édité avec vos org_ids
- [ ] CSV importé (`python import_csv.py`)
- [ ] Token API configuré (`.env`)
- [ ] Cron job testé manuellement (`python main.py`)
- [ ] Dashboard lancé (`npm run dev`)
- [ ] Cron configuré (`crontab -e`)

---

## 🆘 Problèmes ?

### "DATABASE_URL non configurée"
```bash
export DATABASE_URL=postgresql://localhost:5432/alert_client
```

### "No organizations found"
```bash
# Vérifier le CSV
cat database/organizations.csv

# Réimporter
python database/import_csv.py organizations.csv
```

### "SCALEWAY_API_KEY not set"
```bash
# Vérifier le .env
cat cron-match-incidents/.env | grep SCALEWAY
```

### Dashboard ne démarre pas
```bash
cd dashboard
rm -rf node_modules
npm install
npm run dev
```

---

## 📚 Plus d'infos

- `README.md` - Documentation générale
- `README_CSV.md` - Gestion CSV détaillée
- `INSTALL.md` - Guide complet d'installation
- `ARCHITECTURE.md` - Détails techniques