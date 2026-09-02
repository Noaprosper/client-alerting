# Scaleway Client Alerting Dashboard

Dashboard interne pour surveiller les alertes d'incidents pour une **liste spécifique d'organisations**.

## 🎯 Concept

Ce dashboard surveille les incidents pour **uniquement les organisations que vous spécifiez** dans un fichier CSV.

## Architecture

```
┌─────────────────────────────────────┐
│         Incident API                │
│  (incresponse.incre.prd...)         │
│  - GET /core/incidents/             │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   resource_private.v1alpha1         │
│   ConsoleApi.GetFilteredCounters    │
│   - organization_id                  │
│   - products (ResourceCount.Type)   │
│   - localities                      │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│      DB PostgreSQL                  │
│  - incidents                        │
│  - alerts (UNIQUE incident_id,org)  │
│  - organizations (from CSV)         │
│  - sync_logs                        │
│  - v_active_alerts (view)           │
└─────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│    Dashboard - Next.js/React        │
│  - Résumé stats                     │
│  - Grille de cartes clients         │
│  - Filtres (sévérité, client)       │
│  - Liste des alertes                │
└─────────────────────────────────────┘
```

## 📄 Fichier CSV des organisations

### Emplacement
```
/Users/cbenard/Desktop/Alert-client/database/organizations.csv
```

### Format
```csv
org_id,name
11111111-1111-1111-1111-111111111111,Client Alpha
22222222-2222-2222-2222-222222222222,Client Beta
33333333-3333-3333-3333-333333333333,Client Gamma
```

### Comment ajouter vos organisations

1. Ouvrir le fichier CSV :
```bash
nano /Users/cbenard/Desktop/Alert-client/database/organizations.csv
```

2. Ajouter vos org_ids (une par ligne) :
```csv
org_id,name
c5f1a1a1-aaaa-bbbb-cccc-111111111111,Votre Client 1
c5f2a2a2-dddd-eeee-ffff-222222222222,Votre Client 2
```

3. Importer dans la base de données :
```bash
cd /Users/cbenard/Desktop/Alert-client/database
python import_csv.py organizations.csv
```

## Structure du projet

```
Alert-client/
├── database/
│   ├── organizations.csv       # ⭐ VOS ORGANISATIONS ICI
│   ├── import_csv.py           # Script d'import CSV
│   ├── schema.sql              # Schéma de la base de données
│   └── seed_mappings.sql       # Mappings team → resource types
├── cron-match-incidents/
│   ├── main.py                 # Script Python (*/15 * * * *)
│   ├── requirements.txt        # Dépendances Python
│   └── serverless-job.yaml     # Config Serverless
├── dashboard/
│   ├── app/
│   │   ├── page.tsx            # Page principale
│   │   └── api/
│   │       ├── orgs/route.ts   # API: GET /api/orgs
│   │       └── alerts/route.ts # API: GET /api/alerts
│   └── components/
│       ├── OrgCard.tsx         # Carte client
│       └── SummaryStats.tsx    # Stats résumé
└── README.md
```

## Configuration

### Variables d'environnement

Créez un fichier `.env` dans `cron-match-incidents/` et `dashboard/` :

```bash
# API Scaleway (READ-ONLY permissions uniquement!)
SCALEWAY_API_KEY=your_readonly_api_key

# URL de l'API Incident
INCIDENT_API_URL=http://incresponse.incre.prd.fr-par.internal.scaleway.com/core/incidents/

# URL Console API
CONSOLE_API_URL=https://api.scaleway.com/resource-private/v1alpha1

# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/alert_client
```

### ⚠️ Sécurité des tokens

**IMPORTANT**: Le token API Scaleway doit avoir des permissions **READ-ONLY** uniquement :

- ✅ `resource_private.v1alpha1.ConsoleApi:read`
- ✅ `organizations:read`
- ❌ AUCUNE permission d'écriture/suppression

## Installation

### 1. Base de données

```bash
# Créer la base de données
cd /Users/cbenard/Desktop/Alert-client
./init.sh
```

### 2. Importer vos organisations (CSV)

**Éditez le fichier `database/organizations.csv`** avec vos vrais org_ids :

```csv
org_id,name
11111111-1111-1111-1111-111111111111,Client Alpha Corp
22222222-2222-2222-2222-222222222222,Client Beta Industries
33333333-3333-3333-3333-333333333333,Client Gamma Solutions
```

**Importez le CSV** :
```bash
cd database
python import_csv.py organizations.csv
```

### 3. Cron Job

```bash
cd cron-match-incidents
pip install -r requirements.txt

# Tester manuellement
python main.py

# Ajouter au crontab (*/15 * * * *)
crontab -e
# Ajouter: */15 * * * * cd /Users/cbenard/Desktop/Alert-client/cron-match-incidents && python main.py
```

### 4. Dashboard

```bash
cd dashboard
npm install
npm run dev
# Ouvrir http://localhost:3000
```

## Mapping Team → Resource Types

| Team | Resource Types |
|------|---------------|
| compute | instance, instance_gpu, volumes |
| network | public_gateway, ip, vpc, ipam, vpn |
| storage | sbs_volume, sfs_file_system, object_storage |
| database | rdb, redis, mongodb, clickhouse |
| container | kubernetes, containers, registry |
| monitoring | observability_*, grafana |
| iam | iam_*, secret, key |

## API Endpoints

### Dashboard API

- `GET /api/orgs` - Liste des organisations avec stats d'alertes
- `GET /api/alerts?org_id=xxx` - Liste des alertes (filtrable)

### Response Example

```json
[
  {
    "org_id": "11111111-1111-1111-1111-111111111111",
    "name": "Client Alpha Corp",
    "active_alerts_count": 3,
    "highest_severity": "2",
    "distinct_incidents": 2
  }
]
```

## Cron Schedule

- **Fréquence**: Toutes les 15 minutes (`*/15 * * * *`)
- **Timeout**: 5 minutes
- **Logs**: Table `sync_logs`

## Prochaines étapes

1. [ ] Éditer `database/organizations.csv` avec vos vrais org_ids
2. [ ] Importer le CSV: `python database/import_csv.py organizations.csv`
3. [ ] Configurer SCALEWAY_API_KEY dans Secret Manager
4. [ ] Déployer le cron job sur Scaleway Functions
5. [ ] Déployer le dashboard sur Scaleway Containers

## Notes

- La déduplication des alertes est gérée par la contrainte UNIQUE(incident_id, org_id)
- Le dashboard se rafraîche automatiquement chaque minute
- Les tokens API ne doivent JAMAIS avoir de permissions d'écriture
- **Seules les organisations dans le CSV sont surveillées**

## 📚 Documentation

- `QUICKSTART.md` - Guide rapide en 5 minutes ⭐
- `README_CSV.md` - Guide détaillé sur le CSV
- `INSTALL.md` - Installation pas à pas
- `ARCHITECTURE.md` - Détails techniques
# client-alerting
# client-alerting
