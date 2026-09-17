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
TEAM_TO_PRODUCT_TYPES = {'compute': [1], 'network': [13, 14, 15, 24, 30, 36], 'storage': [3, 5, 26, 32], 'database': [7, 18, 27, 34, 35, 41], 'container': [2, 6, 16], 'load_balancer': [3], 'serverless': [17, 18, 28, 29], 'monitoring': [21], 'iam': [9, 22, 23], 'messaging': [20, 39], 'webhosting': [25], 'sre': [1, 2, 3, 5], 'platform': [1, 9], 'dedibox': [15, 25], 'object-storage': [5], 'cloud-compute': [1, 4, 8], 'hardware': [8, 15], 'billing': [1, 3], 'user-accounts': [38, 36], 'internal-services': [11, 15]}
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

def call_api(org_id, ptypes, locality):
    """
    Call Console API dashboard endpoint.
    
    API format: GET /resource-private/v1alpha1/dashboard
    Params: 
      - organization_id (UUID)
      - products (repeated int enum from ResourceCount.Type)
      - localities (repeated int enum from Resource.Locality) - use 1 for all zones
      - strategy (int): 0=unknown, 1=mixed, 2=api, 3=search
    
    Note: The Locality enum only accepts value 1 (all zones) for most products.
    The API returns counts per zone in the response (e.g., {"fr-par-1": 5, "nl-ams-1": 3}).
    For global resources (IAM, etc.), use localities=global.
    """
    if not SCALEWAY_API_KEY: 
        logger.warning('SCALEWAY_API_KEY not set')
        return {}
    try:
        # Use locality=1 for zone-based resources (covers all zones)
        # The API returns breakdown by zone in the response values map
        
        # Build params - products as repeated param, single locality
        params = {
            'organization_id': org_id,
            'products': ptypes,  # requests will encode list as repeated params
            'localities': locality,
            'strategy': 1  # mixed strategy
        }
        
        logger.debug(f'Calling Console API: org={org_id}, products={ptypes}, locality={locality}')
        # CONSOLE_API_URL already includes /dashboard path
        r = requests.get(CONSOLE_API_URL, headers={'X-Auth-Token': SCALEWAY_API_KEY}, params=params, timeout=30)
        r.raise_for_status()
        cnt = {}
        for c in r.json().get('counters', []):
            # Sum all zone values for this resource type
            t = sum(c.get('values', {}).values())
            if t > 0: 
                cnt[c.get('type', 0)] = t
                logger.debug(f'  Resource type {c.get("type")}: {t} resources (zones: {c.get("values")})')
        return cnt
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            logger.warning(f'Permission denied for org {org_id} - check API key permissions')
        elif e.response.status_code == 404:
            logger.warning(f'Endpoint not found for org {org_id}')
        else:
            logger.warning(f'HTTP error for org {org_id}: {e.response.status_code} - {e.response.text}')
        return {}
    except Exception as e:
        logger.warning(f'API error for org {org_id}: {e}')
        return {}

def match_incidents(incs, orgs):
    alerts = []
    for inc in incs:
        rt = TEAM_TO_RESOURCE_TYPES.get(inc.team, [1])
        pt = TEAM_TO_PRODUCT_TYPES.get(inc.team, [1])
        locs = zones_to_localities(inc.impacted_zones)
        logger.info(f'Incident {inc.id}: team={inc.team}, zones={inc.impacted_zones}, locs={locs}')
        for org in orgs:
            cnt = call_api(org, pt, locs)
            matches = [r for r in rt if cnt.get(r, 0) > 0]
            if matches:
                alerts.append(Alert(inc.id, org, matches, locs))
                logger.info(f'Alert: org {org} -> incident {inc.id}')
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
        alerts = match_incidents(incs, orgs)
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
