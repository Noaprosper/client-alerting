#!/usr/bin/env python3
import os, sys, json, logging, re, requests
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import execute_values, Json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INCIDENT_API_URL = os.getenv('INCIDENT_API_URL', 'https://incresponse.incre.prd.fr-par.internal.scaleway.com/core/incidents/')
CONSOLE_API_URL = os.getenv('CONSOLE_API_URL', 'https://api.scaleway.com/resource-private/v1alpha1/dashboard')
# Normalize so the cron works whether CONSOLE_API_URL includes /dashboard or not.
if not CONSOLE_API_URL.endswith('/dashboard'):
    CONSOLE_API_URL = CONSOLE_API_URL.rstrip('/') + '/dashboard'
SCALEWAY_API_KEY = os.getenv('SCALEWAY_API_KEY', '')
DATABASE_URL = os.getenv('DATABASE_URL', '')
REQUEST_TIMEOUT = 300

TEAM_TO_RESOURCE_TYPES = {'compute': [1, 2, 84, 85, 91, 87], 'network': [14, 48, 49, 50, 61, 88, 77, 75, 74, 78, 79, 80, 81, 82, 83, 13, 16], 'storage': [58, 62, 59, 64, 66, 67, 3, 55, 43, 44, 45], 'database': [5, 52, 53, 19, 57, 70, 71, 72, 92], 'container': [7, 17, 32, 6, 31], 'load_balancer': [4, 51], 'serverless': [10, 18, 33, 60, 63], 'monitoring': [68, 89, 24, 25, 26], 'iam': [36, 37, 38, 39, 40, 41, 42, 27, 28, 29, 30, 76, 34, 35], 'messaging': [21, 73, 20], 'webhosting': [22], 'internal-services': [11, 15, 90, 65, 86], 'sre': [1, 7, 4, 3], 'platform': [1, 46, 47, 54], 'dedibox': [16, 22], 'shared-hosting-paas': [22, 17], 'object-storage': [3, 55], 'cloud-compute': [1, 8, 12], 'hardware': [8, 16], 'billing': [1, 3], 'user-accounts': [38, 36]}
# GetFilteredCounters (products/localities) n'est plus utilise : le code appelle
# ConsoleApi.GetDashboard (1 appel/org, matrice complete type x zone), et le
# matching se fait en memoire sur les NOMS de ResourceCount.Type.
TYPE_NAME_TO_ID = {
    'instance': 1, 'instance_gpu': 2, 'object_storage': 3, 'load_balancer': 4,
    'relational_database': 5, 'registry': 6, 'kubernetes': 7, 'baremetal': 8,
    'iot': 9, 'serverless': 10, 'domain': 11, 'apple_silicon': 12,
    'flexible_ip': 13, 'public_gateway': 14, 'smart_labeling': 15, 'dedibox': 16,
    'containers': 17, 'functions': 18, 'redis': 19, 'transactional_email': 20,
    'messaging': 21, 'webhosting': 22, 'observability_token': 24,
    'observability_alert_contact_point': 25, 'observability_grafana_user': 26,
    'secret': 27, 'secret_version': 28, 'key': 29, 'key_version': 30,
    'registry_ns': 31, 'containers_ns': 32, 'functions_ns': 33,
    'managed_key': 34, 'managed_key_version': 35,
    'iam_api_keys': 36, 'iam_ssh_keys': 37, 'iam_users': 38,
    'iam_applications': 39, 'iam_groups': 40, 'iam_policies': 41,
    'iam_permission_sets': 42, 'snapshots': 43, 'images': 44, 'volumes': 45,
    'security_groups': 46, 'placement_groups': 47, 'ip': 48,
    'private_networks': 49, 'vpc': 50, 'load_balancer_ip': 51,
    'rdb_snapshots': 52, 'rdb_backups': 53, 'instance_ip': 54,
    'object_storage_bucket': 55, 'serverless_db': 57, 'sbs_volume': 58,
    'sbs_snapshot': 59, 'serverless_jobs': 60, 'ipam': 61,
    'sbs_volume_storage': 62, 'edge_services_pipeline': 63,
    'sbs_snapshot_storage': 64, 'managed_inference': 65,
    'sfs_file_system': 66, 'sfs_file_system_storage': 67,
    'observability_data_source': 68, 'mongodb': 70, 'mongodb_snapshots': 71,
    'dtwh_clickhouse': 72, 'kafka': 73, 'ili_routing_policy': 74,
    'ili_link': 75, 'key_rotation': 76, 'ili_port': 77, 'ili_loa': 78,
    'ili_connection': 79, 'svpn_vpn_gateways': 80, 'svpn_customer_gateways': 81,
    'svpn_connections': 82, 'svpn_routing_policies': 83,
    'instance_volume_l_ssd': 84, 'instance_volume_scratch': 85,
    'ifr_custom_model': 86, 'autoscaling_group': 87,
    'vpc_peering_connector': 88, 'observability_exporter': 89,
    'datalab': 90, 'instance_template': 91, 'searchdb': 92,
    'gapi_model_usage': 93, 'gapi_batch': 94,
}
TYPE_ID_TO_NAME = {v: k for k, v in TYPE_NAME_TO_ID.items()}
# Team -> noms de ResourceCount.Type (pour le matching GetDashboard en memoire).
TEAM_TO_RESOURCE_TYPE_NAMES = {
    t: [TYPE_ID_TO_NAME[i] for i in ids if i in TYPE_ID_TO_NAME]
    for t, ids in TEAM_TO_RESOURCE_TYPES.items()
}
ZONE_TO_LOCALITY = {'global': 'global', 'FR-PAR': 1, 'FR-PAR-1': 1, 'FR-PAR-2': 1, 'FR-PAR-3': 1, 'IT-MIL': 1, 'IT-MIL-1': 1, 'IT-MIL-2': 1, 'IT-MIL-3': 1, 'ITX4': 1, 'NL-AMS': 1, 'NL-AMS-1': 1, 'NL-AMS-2': 1, 'NL-AMS-3': 1, 'PL-WAW': 1, 'PL-WAW-1': 1, 'PL-WAW-2': 1, 'PL-WAW-3': 1, 'PAR': 1, 'PAR1': 1, 'PAR-1': 1, 'PAR2': 1, 'PAR-2': 1, 'PAR3': 1, 'PAR-3': 1, 'DC2': 1, 'DC3': 1, 'DC5': 1, 'AMS': 1, 'AMS1': 1, 'AMS2': 1, 'AMS3': 1, 'WAW': 1, 'WAW1': 1, 'WAW2': 1, 'WAW3': 1, 'fr-par-1': 1, 'fr-par-2': 1, 'nl-ams-1': 1, 'pl-waw-1': 1}
ZONE_PATTERNS = [r'\b(PAR1|PAR-1|fr-par-1|FR-PAR-1)\b', r'\b(PAR2|PAR-2|fr-par-2|FR-PAR-2)\b', r'\b(PAR3|PAR-3|fr-par-3|FR-PAR-3)\b', r'\b(DC2|DC3|DC5)\b', r'\b(AMS1|AMS-1|nl-ams-1|NL-AMS-1)\b', r'\b(AMS2|AMS-2|nl-ams-2|NL-AMS-2)\b', r'\b(AMS3|AMS-3|nl-ams-3|NL-AMS-3)\b', r'\b(WAW1|WAW-1|pl-waw-1|PL-WAW-1)\b', r'\b(WAW2|WAW-2|pl-waw-2|PL-WAW-2)\b', r'\b(WAW3|WAW-3|pl-waw-3|PL-WAW-3)\b', r'\b(IT-MIL1|IT-MIL-1)\b', r'\b(IT-MIL2|IT-MIL-2)\b', r'\b(IT-MIL3|IT-MIL-3)\b', r'\b(ITX4)\b', r'\b(fr-par)(?!-[0-9])\b', r'\b(it-mil)(?!-[0-9])\b', r'\b(nl-ams)(?!-[0-9])\b', r'\b(pl-waw)(?!-[0-9])\b', r'\b(PAR|AMS|WAW)\b']

@dataclass
class Incident:
    id: int; severity: str; team: str; summary: str; impact: str; is_closed: bool; start_time: str; end_time: Optional[str]; impacted_products: List[str]; impacted_zones: List[str]; comms_channel: Optional[Dict]; report: str; ticket: Optional[str]

@dataclass
class Alert:
    incident_id: int; org_id: str; resource_types: List[int]; localities: List[int]; status: str = 'active'

def get_db_connection():
    if not DATABASE_URL: raise ValueError('DATABASE_URL not set')
    return psycopg2.connect(DATABASE_URL)

def extract_zones_from_text(text):
    if not text: return []
    zones = []
    for p in ZONE_PATTERNS:
        for m in re.findall(p, text.upper(), re.IGNORECASE): zones.append(m.upper())
    # Prefer the specific zone over the bare region of the same region (fr-par-1 > fr-par)
    region_aliases = {'PAR': 'FR-PAR', 'AMS': 'NL-AMS', 'WAW': 'PL-WAW'}
    specific, bare = set(), set()
    for z in zones:
        parts = z.split('-')
        if len(parts) == 3 and parts[2].isdigit():
            specific.add(z)
        else:
            bare.add(z)
    for b in list(bare):
        r = b.rsplit('-', 1)[0] if b.count('-') == 1 else region_aliases.get(b)
        if r and any(s.startswith(r + '-') for s in specific):
            bare.discard(b)
    return sorted(specific | bare)

def zones_to_localities(zones):
    """
    Convert zone names to locality IDs for Console API.
    
    Note: The Console API only accepts locality=1 (all zones) for zone-based resources,
    or locality='global' for global resources (IAM, etc.).
    Returns 1 by default for zone-based resources, 'global' for IAM-related zones.
    """
    if not zones:
        return 1  # Default to all zones
    for z in zones:
        z_upper = z.upper() if z else ''
        # Check for global/IAM resources
        if z_upper in ('GLOBAL', 'IAM'):
            return 'global'
        # Check mapping
        if z_upper in ZONE_TO_LOCALITY:
            return ZONE_TO_LOCALITY[z_upper]
    return 1  # Default to all zones

def fetch_incidents():
    logger.info('Fetching incidents...')
    try:
        r = requests.get(INCIDENT_API_URL, params={'is_closed': 'false', 'limit': 100}, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        incs = []
        for it in r.json().get('results', []):
            txt = f"{it.get('summary', '')} {it.get('impact', '')} {it.get('report', '')}"
            incs.append(Incident(id=it.get('id'), severity=it.get('severity', '4'), team=it.get('team', 'sre'), summary=it.get('summary', ''), impact=it.get('impact', ''), is_closed=it.get('is_closed', False), start_time=it.get('start_time', ''), end_time=it.get('end_time'), impacted_products=it.get('impacted_products', []), impacted_zones=extract_zones_from_text(txt), comms_channel=it.get('comms_channel'), report=it.get('report', ''), ticket=it.get('ticket')))
        logger.info(f'Fetched {len(incs)} incidents')
        return incs
    except Exception as e:
        logger.error(f'Error: {e}')
        return []

def get_organizations(conn):
    with conn.cursor() as cur:
        cur.execute('SELECT org_id FROM organizations')
        return [row[0] for row in cur.fetchall()]

def fetch_console_dashboard(org_id):
    """
    ConsoleApi.GetDashboard: GET /resource-private/v1alpha1/dashboard

    Un SEUL appel par organisation : renvoie la matrice complete type x zone
    (tous les produits). Le matching est ensuite fait en memoire.

    Reponse: {"resource_counts": [{"type": <nom enum>, "values": {zone: count}, ...}]}
    -> {type_name: {zone: count}} en ne gardant que les compteurs > 0.
    """
    if not SCALEWAY_API_KEY:
        logger.warning('SCALEWAY_API_KEY not set')
        return {}
    try:
        # GetDashboard n'accepte ni products ni localities : on recupere tout.
        params = {'organization_id': org_id, 'strategy': 1}  # mixed = 1
        r = requests.get(CONSOLE_API_URL, headers={'X-Auth-Token': SCALEWAY_API_KEY},
                         params=params, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        dash = {}
        for rc in r.json().get('resource_counts', []):
            t = rc.get('type')
            pos = {z: c for z, c in rc.get('values', {}).items() if c > 0}
            if t and pos:
                dash[t] = pos
        logger.info(f'Console dashboard org {org_id}: {len(dash)} resource types with counts')
        return dash
    except requests.exceptions.HTTPError as e:
        resp = e.response
        status = resp.status_code if resp is not None else 0
        if status == 403:
            logger.warning(f'Console API 403 for org {org_id} - check API key permissions')
        elif status == 404:
            logger.warning(f'Console API endpoint not found for org {org_id}')
        else:
            logger.warning(f'Console API HTTP {status} for org {org_id}'
                           + (f': {resp.text}' if resp is not None else ''))
        return {}
    except Exception as e:
        logger.warning(f'Console API error for org {org_id}: {e}')
        return {}

def match_incidents(incs, orgs, dashboards):
    """Match incidents against per-org GetDashboard payloads (fetched once per run).

    Un alert est cree quand un type de la team de l'incident a un count > 0
    dans l'organisation (n'importe quelle zone). Les localities restent
    derivees du texte de l'incident (a posteriori on pourra affiner par zone).
    """
    alerts = []
    for inc in incs:
        type_names = TEAM_TO_RESOURCE_TYPE_NAMES.get(inc.team, [])
        locs = zones_to_localities(inc.impacted_zones)
        logger.info(f'Incident {inc.id}: team={inc.team}, zones={inc.impacted_zones}, '
                    f'locs={locs}, types={type_names}')
        for org in orgs:
            dash = dashboards.get(org, {})
            if not dash:
                continue
            matched = [TYPE_NAME_TO_ID[n] for n in type_names if dash.get(n)]
            if matched:
                alerts.append(Alert(inc.id, org, matched, locs))
                logger.info(f'Alert: org {org} -> incident {inc.id} (types {matched})')
    return alerts

def save_incidents(conn, incs):
    with conn.cursor() as cur:
        data = [(i.id, i.severity, i.team, i.summary, i.impact, i.is_closed, i.start_time, i.end_time, Json(i.impacted_products), Json(i.impacted_zones), Json(i.comms_channel), i.report, i.ticket, Json({}), Json({})) for i in incs]
        execute_values(cur, "INSERT INTO incidents (incident_id, severity, team, summary, impact, is_closed, start_time, end_time, impacted_products, impacted_zones, comms_channel, report, ticket, lead, reporter) VALUES %s ON CONFLICT (incident_id) DO UPDATE SET severity=EXCLUDED.severity, team=EXCLUDED.team, summary=EXCLUDED.summary, impact=EXCLUDED.impact, is_closed=EXCLUDED.is_closed, end_time=EXCLUDED.end_time, impacted_zones=EXCLUDED.impacted_zones, updated_at=CURRENT_TIMESTAMP", data)
    conn.commit()
    logger.info(f'Saved {len(incs)} incidents')

def save_alerts(conn, alerts):
    with conn.cursor() as cur:
        data = [(a.incident_id, a.org_id, Json(a.resource_types), Json(a.localities), a.status) for a in alerts]
        execute_values(cur, "INSERT INTO alerts (incident_id, org_id, resource_types, localities, status) VALUES %s ON CONFLICT (incident_id, org_id) DO UPDATE SET resource_types=EXCLUDED.resource_types, localities=EXCLUDED.localities, status=EXCLUDED.status, updated_at=CURRENT_TIMESTAMP", data)
    conn.commit()
    logger.info(f'Saved {len(alerts)} alerts')

def log_sync(conn, t, s, n, err=None, dur=0):
    with conn.cursor() as cur:
        cur.execute('INSERT INTO sync_logs (sync_type, status, records_processed, error_message, duration_ms) VALUES (%s, %s, %s, %s, %s)', (t, s, n, err, dur))
    conn.commit()

def main():
    start = datetime.now(timezone.utc)
    logger.info('Starting match-incidents')
    try:
        conn = get_db_connection()
        incs = fetch_incidents()
        if not incs:
            log_sync(conn, 'match-incidents', 'success', 0, dur=int((datetime.now(timezone.utc)-start).total_seconds()*1000))
            return
        save_incidents(conn, incs)
        orgs = get_organizations(conn)
        logger.info(f'Found {len(orgs)} organizations')
        if not orgs:
            log_sync(conn, 'match-incidents', 'warning', 0, err='No organizations')
            return
        # GetDashboard : 1 appel par org, puis matching en memoire pour tous les incidents.
        dashboards = {org: fetch_console_dashboard(org) for org in orgs}
        alerts = match_incidents(incs, orgs, dashboards)
        save_alerts(conn, alerts)
        dur = int((datetime.now(timezone.utc)-start).total_seconds()*1000)
        log_sync(conn, 'match-incidents', 'success', len(alerts), dur=dur)
        logger.info(f'Done: {len(alerts)} alerts in {dur}ms')
    except Exception as e:
        logger.error(f'Failed: {e}', exc_info=True)
        try:
            conn = get_db_connection()
            log_sync(conn, 'match-incidents', 'error', 0, err=str(e))
        except: pass
        sys.exit(1)

if __name__ == '__main__':
    main()
