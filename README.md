# Client Alerting Dashboard

Dashboard interne pour surveiller les alertes d'incidents pour une **liste spécifique d'organisations**.

## Le but :

Le dashboard surveille les incidents pour **uniquement les organisations spécifiées** dans un fichier CSV.

## Comment ca fonctionne : 

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
│   - organization_id                 │
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



## Fichier CSV des organisations



### Emplacement

```
/Users/cbenard/Desktop/Alert-client/database/organizations.csv
```

  
*Fichier aussi sur GitHub

### Format

```csv
org_id,name
11111111-1111-1111-1111-111111111111,Client Alpha
22222222-2222-2222-2222-222222222222,Client Beta
33333333-3333-3333-3333-333333333333,Client Gamma
```



### Ajout des Org-ID

Importer dans la base de données :

```bash
cd /Users/cbenard/Desktop/Alert-client/database
python import_csv.py organizations.csv
```



## Structure du projet

```
Alert-client/
├── database/
│   ├── organizations.csv       
│   ├── import_csv.py           
│   ├── schema.sql              
│   └── seed_mappings.sql       
├── cron-match-incidents/
│   ├── main.py                 
│   ├── requirements.txt        
│   └── serverless-job.yaml     
├── dashboard/
│   ├── app/
│   │   ├── page.tsx            
│   │   └── api/
│   │       ├── orgs/route.ts   
│   │       └── alerts/route.ts 
│   └── components/
│       ├── OrgCard.tsx         
│       └── SummaryStats.tsx    
└── README.md
```



## Configuration



### Variables d'environnement

Créez un fichier `.env` dans `cron-match-incidents/` et `dashboard/` :

```bash
# API Scaleway (READ-ONLY permissions uniquement!)
SCALEWAY_API_KEY=your_readonly_api_key

# URL de l'API Incident
INCIDENT_API_URL=https://incresponse.incre.prd.fr-par.internal.scaleway.com/core/incidents/

# URL Console API
CONSOLE_API_URL=https://api.scaleway.com/resource-private/v1alpha1/dashboard

# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/alert_client
```



### Sécurité des tokens

Crutial : Le token API a des accès Read et Write

## Installation

### 1. Créer la base de données

### 2. Importer les organisations (CSV)

**Éditer le fichier** `database/organizations.csv` avec les vraies org_ids :

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


| Team       | Resource Types                              |
| ---------- | ------------------------------------------- |
| compute    | instance, instance_gpu, volumes             |
| network    | public_gateway, ip, vpc, ipam, vpn          |
| storage    | sbs_volume, sfs_file_system, object_storage |
| database   | rdb, redis, mongodb, clickhouse             |
| container  | kubernetes, containers, registry            |
| monitoring | observability_*, grafana                    |
| iam        | iam_*, secret, key                          |




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

- **Fréquence**: Toutes les 15 minutes (`*/15 * * `* *)
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
- **Seules les organisations dans le CSV sont surveillées**



## Documentation

- `QUICKSTART.md` - Guide rapide en 5 minutes 
- `README_CSV.md` - Guide détaillé sur le CSV
- `INSTALL.md` - Installation pas à pas
- `ARCHITECTURE.md` - Détails techniques

