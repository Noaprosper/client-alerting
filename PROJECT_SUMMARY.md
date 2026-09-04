# Résumé du Projet - Scaleway Client Alerting Dashboard



###  Arborescence complète

```
/Users/cbenard/Desktop/Alert-client/
├── 📄 README.md                    # Documentation générale
├── 📄 INSTALL.md                   # Guide d'installation pas à pas
├── 📄 ARCHITECTURE.md              # Détails techniques et architecture
├── 📄 PROJECT_SUMMARY.md           # Ce fichier
├── 📄 .env.example                 # Exemple de variables d'environnement
├── 📄 .gitignore                   # Fichiers à ignorer (git)
├── 🔧 init.sh                      # Script d'initialisation
│
├── 🗄️ database/
│   ├── schema.sql                  # Schéma PostgreSQL (4 tables + 1 vue)
│   ├── seed_mappings.sql           # Mappings TEAM → RESOURCE_TYPES
│   ├── organizations.csv           # ⭐ VOS ORGANISATIONS (à éditer)
│   ├── organizations.csv.example   # Exemple de CSV
│   ├── import_csv.py               # Script d'import CSV
│   └── seed_organizations.sql      # Seed manuel (optionnel)
│
├── ⏰ cron-match-incidents/
│   ├── main.py                     # Script Python (342 lignes)
│   ├── requirements.txt            # Dépendances Python (requests, psycopg2)
│   └── serverless-job.yaml         # Config déploiement Serverless
│
└── 🖥️ dashboard/
    ├── package.json                # Dépendances Next.js
    ├── tsconfig.json               # Config TypeScript
    ├── next.config.js              # Config Next.js
    ├── app/
    │   ├── layout.tsx              # Layout principal
    │   ├── page.tsx                # Page dashboard (grille + alerts)
    │   └── api/
    │       ├── orgs/route.ts       # GET /api/orgs
    │       └── alerts/route.ts     # GET /api/alerts
    └── components/
        ├── OrgCard.tsx             # Carte client
        └── SummaryStats.tsx        # Stats résumé
```



## 🎯 Fonctionnalités implémentées



### 1. Cron Job (`match-incidents`)

- ✅ Récupère les incidents ouverts depuis l'Incident API
- ✅ Map les teams vers les ResourceCount.Type
- ✅ Map les zones vers les Localities
- ✅ Appelle GetFilteredCounters pour chaque organisation (depuis CSV)
- ✅ Crée des alertes si resources > 0
- ✅ Déduplication via UNIQUE(incident_id, org_id)
- ✅ Logs d'exécution dans sync_logs
- ✅ Schedule: */15 * * * * (toutes les 15 min)
- ✅ Timeout: 5 minutes



### 2. Base de données (PostgreSQL)

- ✅ Table `organizations` - Clients (importés depuis CSV)
- ✅ Table `incidents` - Incidents depuis l'API
- ✅ Table `alerts` - Alertes (avec contrainte UNIQUE)
- ✅ Table `sync_logs` - Logs d'exécution
- ✅ Vue `v_active_alerts` - Alertes actives
- ✅ Vue `v_org_alert_summary` - Stats par org



### 3. Dashboard (Next.js/React)

- ✅ Page d'accueil avec stats résumé
- ✅ Grille de cartes clients (OrgCard)
- ✅ Filtres par sévérité
- ✅ Liste des alertes actives
- ✅ Rafraîchissement automatique (1 min)
- ✅ API routes: /api/orgs, /api/alerts
- ✅ Composants réutilisables



### 4. Gestion CSV

- ✅ Fichier `organizations.csv` pour gérer les clients
- ✅ Script `import_csv.py` pour importer dans la DB
- ✅ Fichier d'exemple `organizations.csv.example`
- ✅ Mise à jour facile sans modifier le code



### 4. Mappings

- ✅ 20 teams → ResourceCount.Type
- ✅ Zones → Localities
- ✅ 20 organisations exemples



### Secrets

- Les tokens doivent être stockés dans Secret Manager
- Ne jamais committer les fichiers `.env`
- Utiliser des variables d'environnement



## Prochaines étapes



### À faire manuellement

1. **Configurer la base de données**
  ```bash
   cd /Users/cbenard/Desktop/Alert-client
   ./init.sh
  ```
2. **Ajouter les vrais clients (CSV)**
  - Éditer: `database/organizations.csv`
  - Remplacer par vos vrais org_ids
  - Importer: `python database/import_csv.py organizations.csv`
3. **Configurer les APIs**
  - Créer un fichier `.env` dans `cron-match-incidents/`
  - Ajouter SCALEWAY_API_KEY (READ-ONLY)
  - Ajouter DATABASE_URL
  - Tester: `python main.py`
4. **Déployer le dashboard**
  ```bash
   cd dashboard
   npm install
   npm run dev
  ```
5. **Configurer le cron**
  ```bash
   crontab -e
   # Ajouter: */15 * * * * cd /Users/cbenard/Desktop/Alert-client/cron-match-incidents && source venv/bin/activate && python main.py
  ```



## 📊 Stats du projet


| Métrique                  | Valeur |
| ------------------------- | ------ |
| Fichiers créés            | 17     |
| Lignes de code Python     | ~342   |
| Lignes de code TypeScript | ~400   |
| Lignes SQL                | ~200   |
| Tables DB                 | 4      |
| Vues DB                   | 2      |
| Composants React          | 2      |
| API Routes                | 2      |
| Teams mappées             | 20     |
| Resource Types            | 50+    |
| Organisations (exemples)  | 20     |




## Technologies utilisées



### Backend

- Python 3.9+
- PostgreSQL 13+
- requests (HTTP)
- psycopg2 (DB)



### Frontend

- Next.js 14
- React 18
- TypeScript 5
- Tailwind CSS (via classes utilitaires)



### Infrastructure

- Cron (*/15 * * * *)
- Scaleway Console API
- Scaleway Incident API
- Scaleway Secret Manager (recommandé)



