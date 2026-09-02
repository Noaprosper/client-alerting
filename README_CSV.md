# Gestion des Organisations via CSV

## 📄 Fichier CSV

Au lieu d'avoir toutes les organisations en dur dans le code, vous pouvez gérer votre liste d'organisations via un fichier CSV.

### Emplacement
```
/Users/cbenard/Desktop/Alert-client/database/organizations.csv
```

### Format du fichier

```csv
org_id,name
11111111-1111-1111-1111-111111111111,Client Alpha
22222222-2222-2222-2222-222222222222,Client Beta
33333333-3333-3333-3333-333333333333,Client Gamma
```

### Colonnes requises

| Colonne | Type | Description |
|---------|------|-------------|
| `org_id` | UUID | L'ID de l'organisation Scaleway |
| `name` | String | Nom affiché dans le dashboard |

## 📥 Importer les organisations

### Option 1: Script Python (recommandé)

```bash
cd /Users/cbenard/Desktop/Alert-client/database

# Modifier le fichier CSV
nano organizations.csv

# Importer dans la base de données
python import_csv.py organizations.csv
```

### Option 2: Commande SQL COPY

```bash
psql -d alert_client -c "COPY organizations(org_id, name) FROM '/Users/cbenard/Desktop/Alert-client/database/organizations.csv' CSV HEADER;"
```

### Option 3: Inserts SQL manuels

Éditer `database/seed_organizations.sql` et remplacer par vos INSERT:

```sql
INSERT INTO organizations (org_id, name) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Client Alpha'),
    ('22222222-2222-2222-2222-222222222222', 'Client Beta')
ON CONFLICT (org_id) DO NOTHING;
```

Puis exécuter:
```bash
psql -d alert_client -f database/seed_organizations.sql
```

## 🔄 Mettre à jour la liste

### Ajouter un client
1. Ouvrir `database/organizations.csv`
2. Ajouter une nouvelle ligne
3. Exécuter: `python import_csv.py organizations.csv`

### Supprimer un client
1. Ouvrir `database/organizations.csv`
2. Supprimer la ligne
3. Exécuter: `python import_csv.py organizations.csv` (le script fait TRUNCATE avant)

### Modifier un nom
1. Ouvrir `database/organizations.csv`
2. Modifier le nom
3. Exécuter: `python import_csv.py organizations.csv`

## 📊 Vérifier les organisations

```bash
# Via psql
psql -d alert_client -c "SELECT * FROM organizations ORDER BY name;"

# Via le script
python import_csv.py organizations.csv
```

## 🔐 Exemple de fichier CSV complet

```csv
org_id,name
c5f1a1a1-1111-1111-1111-111111111111,Mon Client SAS
c5f2a2a2-2222-2222-2222-222222222222,Startup Tech
c5f3a3a3-3333-3333-3333-333333333333,Entreprise Globale
c5f4a4a4-4444-4444-4444-444444444444,Société Digitale
c5f5a5a5-5555-5555-5555-555555555555,Service Cloud
```

## ⚙️ Utilisation dans le cron job

Le cron job lit automatiquement les organisations depuis la base de données. Après avoir importé votre CSV, le cron job utilisera automatiquement la nouvelle liste.

```bash
# Le cron job fait ceci:
# 1. Lit toutes les orgs dans la table organizations
# 2. Pour chaque incident, appelle GetFilteredCounters pour chaque org
# 3. Crée des alertes si des ressources correspondent

# Pas besoin de redémarrer quoi que ce soit !
```

## 📝 Notes

- Le script `import_csv.py` fait un TRUNCATE avant d'importer (remplace toute la liste)
- Les alertes existantes sont conservées (clés étrangères avec CASCADE)
- Vous pouvez avoir autant d'organisations que nécessaire dans le CSV
- Le dashboard se met à jour automatiquement (refresh 1 min)