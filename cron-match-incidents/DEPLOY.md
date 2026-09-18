# Deploy — Alert-client (match-incidents)

Documentation du déploiement corrigé (aligné sur la logique projet :
`CRON → container → Incident API + Console API → base schema.sql → dashboard`).

## Architecture cible (FR-PAR)

```
CRON (*/15 * * * *)  ──►  Serverless Container « match-incidents »
                                 │  image rg.fr-par.scw.cloud/rg-alert-client/match-incidents:latest (amd64)
                                 │  port 8080 / http1 · scale 0→1 · timeout 300s · privacy public
                                 │  Private Network : b53126a5-… (→ RDB privé 10.11.0.2:5432)
                                 ▼
                    +  Incident API  GET /core/incidents/   (INCIDENT_API_URL)
                    +  Console API   GET /dashboard         (CONSOLE_API_URL, ConsoleApi.GetFilteredCounters)
                                 ▼
                    RDB rdb-alert-client (PostgreSQL-17) : organizations / incidents / alerts / sync_logs
                                 ▼
                    Dashboard (Next.js/React) : stats · grille clients · filtres · liste alertes
```

## Container actuel

- ID          : `3534c460-92e9-4527-9522-e7c0fba87d66`
- Nom         : `match-incidents`
- Domaine     : `https://cnsalertclient3dfaaa4e-match-incidents.functions.fnc.fr-par.scw.cloud`
- Statut      : `ready`

### Variables d'environnement (env, non sensibles)
```
INCIDENT_API_URL = https://incresponse.incre.prd.fr-par.internal.scaleway.com/core/incidents/
CONSOLE_API_URL  = https://api.scaleway.com/resource-private/v1alpha1/dashboard
```

### Secrets montés (secret-environment-variables → valeurs littérales dans la config container)
```
DATABASE_URL     = postgresql://root:<PWD-URL-ENCODED>@10.11.0.2:5432/rdb   (endpoint PRIVÉ du RDB)
SCALEWAY_API_KEY = clé API (>= read-only ConsoleApi + organizations)
```

## Secrets « Secret Manager » (noms canoniques)

| Nom                          | Rôle                                                        |
|------------------------------|-------------------------------------------------------------|
| `alert-client-access-key`    | ACCESS key id (ex `SCW633…`) — doc, non monté dans le container |
| `alert-client-database-url`  | DATABASE_URL — endpoint **privé** `10.11.0.2:5432` (rev4 active) |
| `alert-client-db-password`   | mot de passe RDB                                           |
| `alert-client-scaleway-key`  | SECRET key (header X-Auth-Token)                            |

> ⚠️ Contraintes importantes :
> - La `value` d'un secret-env container est la **valeur littérale** (le CLI envoie
>   `{"key":…,"value":…}` à l'API) : on y met donc la valeur réelle, pas un UUID.
> - Le mot de passe du DSN contient des caractères spéciaux (`Mo:h0M…`) : il doit être
>   **URL-encodé** dans le DSN (`%3A`, `%7C`…), sinon psycopg2 casse (`invalid integer … for option "port"`).
> - Le database-url était en **public** (`51.159.11.135:11505`, pour le dev local) : le
>   container utilise maintenant le **privé** (10.11.0.2). Le dev local garde l'URL publique
>   dans `.env`.

## Build / Push de l'image (depuis `cron-match-incidents/`)
```bash
cd cron-match-incidents
docker login rg.fr-par.scw.cloud -u <ACCESS_KEY> --password-stdin <<< <SECRET_KEY>
docker build --platform linux/amd64 -t rg.fr-par.scw.cloud/rg-alert-client/match-incidents:latest .
docker push  rg.fr-par.scw.cloud/rg-alert-client/match-incidents:latest
```
Le container doit être **amd64** ; la règle de déploiement est `:latest`.
Le wrapper HTTP (`server.py`) exécute `main.main()` à chaque invocation et renvoie
`200` (rc=0) / `500` (rc≠0).

## CRON
- ID       : `a6319918-52a7-468f-94db-0012a37e9b88`
- Schedule : `*/15 * * * *` (toutes les 15 minutes)
- Cible    : container `match-incidents` (3534c460-…)

```bash
scw container cron create container-id=3534c460-92e9-4527-9522-e7c0fba87d66 schedule='*/15 * * * *' name=match-incidents-cron
```

## Vérification
```bash
curl https://cnsalertclient3dfaaa4e-match-incidents.functions.fnc.fr-par.scw.cloud/
# attendu : rc=0 + logs ; la ligne rc=1 => erreur (voir le corps HTTP)
# vérifier la base : SELECT ... FROM sync_logs ORDER BY id DESC LIMIT 5;
```

## Points restants (acteurs humains / réseau)
1. **`database/organizations.csv`** : remplacer les IDs factices par les **vrais org_id**
   clients, puis `scw db` import → `python3 import_csv.py organizations.csv`
   (ou psql). Sans organisations, le job logue `warning No organizations` (rc=0).
2. **Incident API** : à ce jour `incresponse.incre.prd.fr-par.internal.scaleway.com`
   **ne résout pas depuis le container** (DNS du réseau Serverless). Sur un poste
   Scaleway/VPN il résout vers `10.40.140.0:443`. Il faut exposer/permettre l'accès
   réseau du container à ce service interne (listé « à corriger » en attente d'infra),
   sinon `fetch_incidents` renvoie `[]` (le job reste `success` avec 0 incident).
3. **IAM** : la clé montée doit rester **read-only** (ConsoleApi `get` + `organizations` `read`).
