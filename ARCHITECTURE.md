# Architecture - Scaleway Client Alerting Dashboard

## Vue d'ensemble

Système de surveillance des incidents qui corrèle les incidents ouverts avec les ressources des clients pour générer des alertes ciblées.

## Flux de données

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Incident API   │────▶│  match-incidents     │────▶│  PostgreSQL DB  │
│  (Django REST)  │     │  (cron */15 * * * *) │     │  (4 tables + 2  │
└─────────────────┘     └──────────────────────┘     │     vues)       │
                                                      └────────┬────────┘
┌─────────────────┐                                          │
│  Console API    │──────────────────────────────────────────┤
│  GetDashboard   │                                          │
│                 │◀─────────────────────────────────────────┤
└─────────────────┘                                          │
                                                      ┌────────▼────────┐
                                                      │   Dashboard     │
                                                      │   (Next.js)     │
                                                      └─────────────────┘
```

## Composants

### 1. Cron Job (`match-incidents`)

**Schedule**: `*/15 * * * *` (toutes les 15 minutes)  
**Timeout**: 5 minutes

**Étapes**:
1. Fetch incidents ouverts (`is_closed=false`) depuis Incident API
2. Charger les organisations depuis la DB (importées via CSV)
3. Pour chaque organisation (depuis CSV):
   - Appeler `GetDashboard(org_id)` **une seule fois** (matrice complète `resource_counts`)
4. Pour chaque incident:
   - Mapper `team` → noms de `ResourceCount.Type`
   - Mapper `zone` → `Locality`
   - Matcher en mémoire: créer Alert si un type de la team a count > 0 dans l'org
5. Déduplication via contrainte UNIQUE(incident_id, org_id)

**Clés de mapping**:

```python
TEAM_TO_RESOURCE_TYPES = {
    'compute': [1, 2, 84, 85],      # ids ResourceCount.Type
    'network': [14, 48, 49, 50],    # ids ResourceCount.Type
    'database': [5, 19, 70],        # ids ResourceCount.Type
    # ... voir main.py pour la liste complète
}

# Le matching GetDashboard se fait sur les NOMS des types :
# main.py derive TEAM_TO_RESOURCE_TYPE_NAMES via TYPE_ID_TO_NAME
# (ex: 7 -> 'kubernetes', 4 -> 'load_balancer', 5 -> 'relational_database')
```

### 2. API Console (`resource_private.v1alpha1.ConsoleApi.GetDashboard`)

**Endpoint**: `GET /resource-private/v1alpha1/dashboard`

Ce RPC retourne la matrice complète type × zone pour une organisation
(tous les produits) — c'est l'API utilisée par la console. Le code l'appelle
**une seule fois par organisation**, puis fait le matching en mémoire.

**Paramètres** (GetDashboard ne prend PAS `products`/`localities`):
- `organization_id` (UUID) — ou `project_id`
- `strategy` (DataSourceStrategy) - 1=mixed

**Réponse** (`Dashboard.resource_counts`, types rendus par **nom** d'enum):

```json
{
  "resource_counts": [
    {"type": "kubernetes", "values": {"fr-par": 2, "it-mil": 0, "nl-ams": 0, "pl-waw": 0}, "unit": "none", "warning": "no_warning", "has_error": false, "prevent_delete": true},
    {"type": "load_balancer", "values": {"fr-par-1": 2, "fr-par-2": 1}, "unit": "none", "warning": "no_warning", "has_error": false, "prevent_delete": true}
  ]
}
```

⚠️ `GetFilteredCounters` (`/resource-private/v1alpha1/filtered-counters`) est un
RPC distinct qui exige `products` + `localities` (min 1 chacun) — non utilisé ici.

### 3. Base de données (PostgreSQL)

**Tables**:

```sql
organizations  -- Importées depuis CSV
├── org_id (UUID PRIMARY KEY)
├── name (VARCHAR)
└── created_at

incidents
├── id (SERIAL PK)
├── incident_id (INTEGER UNIQUE)  # ID Incident API
├── severity, team, summary, impact
├── is_closed, start_time, end_time
└── JSONB: impacted_products, impacted_zones, comms_channel

alerts
├── id (UUID PK)
├── incident_id (FK → incidents)
├── org_id (FK → organizations)
├── resource_types (INTEGER[])
├── localities (INTEGER[])
├── status, created_at
└── UNIQUE(incident_id, org_id)  # Déduplication

sync_logs
├── id (UUID PK)
├── sync_type, status
├── records_processed, error_message
└── started_at, duration_ms
```

**Vues**:
- `v_active_alerts` - Alertes actives avec détails
- `v_org_alert_summary` - Stats par organisation

### 4. Dashboard (Next.js)

**Pages**:
- `/` - Vue principale avec grille de cartes clients

**API Routes**:
- `GET /api/orgs` - Liste orgs avec stats
- `GET /api/alerts?org_id=xxx` - Alertes filtrées

**Composants**:
- `OrgCard` - Carte client avec sévérité
- `SummaryStats` - Stats globales

## Gestion des organisations (CSV)

### Fichier CSV

**Emplacement**: `database/organizations.csv`

**Format**:
```csv
org_id,name
11111111-1111-1111-1111-111111111111,Client Alpha
22222222-2222-2222-2222-222222222222,Client Beta
```

### Import

```bash
cd database
python import_csv.py organizations.csv
```

Le script:
1. Lit le fichier CSV
2. Importe/met à jour toutes les lignes du CSV (upsert)
3. Supprime les organisations qui ne sont plus dans le CSV
   (ON DELETE CASCADE nettoie leurs alertes)
4. Les alertes des organisations maintenues dans la liste sont conservées

### Mise à jour

Pour ajouter/supprimer des clients:
1. Éditer `database/organizations.csv`
2. Réexécuter `python import_csv.py organizations.csv`
3. Le cron job utilisera automatiquement la nouvelle liste

## Sécurité

### Permissions API Scaleway

**⚠️ CRITIQUE**: Le token API doit être **READ-ONLY**

Politique IAM recommandée:
```json
{
  "permissions": [
    {
      "resource": "resource_private.v1alpha1.ConsoleApi",
      "actions": ["get"]
    },
    {
      "resource": "organizations",
      "actions": ["read"]
    }
  ]
}
```

**Ne JAMAIS accorder**:
- ❌ write
- ❌ delete
- ❌ create
- ❌ update

### Secrets

Les secrets doivent être stockés dans Scaleway Secret Manager:
- `alert-client-scaleway-key`
- `alert-client-database-url`

## Matching Logic

Le coeur du système est le matching entre:
1. **Incident** → team + zones impactées
2. **Organization** → ressources par type + localité

**Exemple**:
```
Incident #123:
  team: "database"
  impacted_zones: ["fr-par-1"]

Organization "Client A":
  GetDashboard(org_id)
  → resource_counts: {"kubernetes": {"fr-par": 2}, "relational_database": {...}, ...}

Résultat:
  → Alerte créée si un type de la team "database" a count > 0 chez Client A
```

## Monitoring

### Métriques à suivre

- Temps d'exécution du cron job (< 5 min)
- Nombre d'alertes créées par exécution
- Taux d'erreur API
- Dernière sync réussie

### Logs

Table `sync_logs`:
```sql
SELECT * FROM sync_logs 
ORDER BY started_at DESC 
LIMIT 10;
```

## Évolutions futures

- [ ] Notifications email/Slack
- [ ] Historique des alertes (resolved_at)
- [ ] Dashboard par client (vue individuelle)
- [ ] Export CSV/PDF
- [ ] Webhook pour intégrations
