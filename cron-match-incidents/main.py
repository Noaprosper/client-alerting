#!/usr/bin/env python3
"""
Match Incidents Cron Job
Runs every 15 minutes to:
1. Fetch open incidents from Incident API
2. For each incident, map team to ResourceCount.Type
3. For each organization, call GetFilteredCounters
4. Create alerts if resources match
5. Deduplicate using UNIQUE constraint
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import execute_values, Json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
INCIDENT_API_URL = os.getenv('INCIDENT_API_URL', 'http://incresponse.incre.prd.fr-par.internal.scaleway.com/core/incidents/')
CONSOLE_API_URL = os.getenv('CONSOLE_API_URL', 'https://api.scaleway.com/resource-private/v1alpha1')
SCALEWAY_API_KEY = os.getenv('SCALEWAY_API_KEY', '')
DATABASE_URL = os.getenv('DATABASE_URL', '')

# Timeout settings
REQUEST_TIMEOUT = 300  # 5 minutes as per architecture

# Team to ResourceCount.Type mapping
TEAM_TO_RESOURCE_TYPES: Dict[str, List[int]] = {
    'compute': [1, 2, 84, 85, 91, 87],
    'network': [14, 48, 49, 50, 61, 88, 77, 75, 74, 78, 79, 80, 81, 82, 83, 13, 16],
    'storage': [58, 62, 59, 64, 66, 67, 3, 55, 43, 44, 45],
    'database': [5, 52, 53, 19, 57, 70, 71, 72, 92],
    'container': [7, 17, 32, 6, 31],
    'load_balancer': [4, 51],
    'serverless': [10, 18, 33, 60, 63],
    'monitoring': [68, 89, 24, 25, 26],
    'iam': [36, 37, 38, 39, 40, 41, 42, 27, 28, 29, 30, 76, 34, 35],
    'messaging': [21, 73, 20],
    'webhosting': [22],
    'internal-services': [11, 15, 90, 65, 86],
    'sre': [1, 7, 4, 3],
    'platform': [1, 46, 47, 54],
    'dedibox': [16, 22],
    'shared-hosting-paas': [22, 17],
    'object-storage': [3, 55],
    'cloud-compute': [1, 8, 12],
    'hardware': [8, 16],
    'billing': [1, 3],
    'user-accounts': [38, 36],
}

TEAM_TO_PRODUCT_TYPES: Dict[str, List[int]] = {
    'compute': [1],
    'network': [13, 14, 15, 24, 30, 36],
    'storage': [3, 5, 26, 32],
    'database': [7, 18, 27, 34, 35, 41],
    'container': [2, 6, 16],
    'load_balancer': [3],
    'serverless': [17, 18, 28, 29],
@dataclass
class Incident:
    id: int
    severity: str
    team: str
    summary: str
    impact: str
    is_closed: bool
    start_time: str
    end_time: Optional[str]
    impacted_products: List[str]
    impacted_zones: List[str]
    comms_channel: Optional[Dict]
    report: str
    ticket: Optional[str]


@dataclass
class Alert:
    incident_id: int
    org_id: str
    resource_types: List[int]
    localities: List[int]
    status: str = 'active'


def get_db_connection():
    """Create database connection from DATABASE_URL"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def fetch_incidents() -> List[Incident]:
    """Fetch open incidents from Incident API"""
    logger.info("Fetching open incidents from Incident API...")
    
    try:
        params = {'is_closed': 'false', 'limit': 100}
        response = requests.get(INCIDENT_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        incidents = []
        
        for item in data.get('results', []):
            incident = Incident(
                id=item.get('id'),
                severity=item.get('severity', '4'),
                team=item.get('team', 'sre'),
                summary=item.get('summary', ''),
                impact=item.get('impact', ''),
                is_closed=item.get('is_closed', False),
                start_time=item.get('start_time', ''),
                end_time=item.get('end_time'),
                impacted_products=item.get('impacted_products', []),
                impacted_zones=item.get('impacted_zones', []),
                comms_channel=item.get('comms_channel'),
                report=item.get('report', ''),
                ticket=item.get('ticket')
            )
            incidents.append(incident)
        
        logger.info(f"Fetched {len(incidents)} open incidents")
def get_organizations(conn) -> List[str]:
    """Get all organization IDs from database"""
    with conn.cursor() as cur:
        cur.execute("SELECT org_id FROM organizations")
        return [row[0] for row in cur.fetchall()]


def load_organizations_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """Load organizations from CSV file"""
    import csv
    orgs = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                org_id = row.get('org_id', '').strip()
                name = row.get('name', '').strip()
                if org_id:
                    orgs.append({'org_id': org_id, 'name': name})
        
        logger.info(f"Loaded {len(orgs)} organizations from CSV")
        return orgs
        
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return []


def call_get_filtered_counters(org_id: str, product_types: List[int], localities: List[int]) -> Dict[str, int]:
def call_get_filtered_counters(org_id: str, product_types: List[int], localities: List[int]) -> Dict[str, int]:
    """Call ConsoleApi.GetFilteredCounters for a specific organization"""
    if not SCALEWAY_API_KEY:
        logger.warning("SCALEWAY_API_KEY not set, skipping API call")
        return {}
    
    try:
        headers = {'X-Auth-Token': SCALEWAY_API_KEY, 'Content-Type': 'application/json'}
        
        params = {
            'organization_id': org_id,
            'products': product_types,
            'localities': localities,
            'strategy': 1
        }
        
        response = requests.get(
            f"{CONSOLE_API_URL}/filtered-counters",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        counters = {}
        
        for counter in data.get('counters', []):
            type_id = counter.get('type', 0)
            values = counter.get('values', {})
            total = sum(values.values()) if values else 0
            if total > 0:
                counters[type_id] = total
        
        return counters
        
    except Exception as e:
        logger.warning(f"Error calling GetFilteredCounters for {org_id}: {e}")
        return {}


def match_incidents_to_orgs(incidents: List[Incident], org_ids: List[str]) -> List[Alert]:
    """Match incidents to organizations based on resource types and localities"""
    alerts = []
    
    for incident in incidents:
        resource_types = TEAM_TO_RESOURCE_TYPES.get(incident.team, [1])
        product_types = TEAM_TO_PRODUCT_TYPES.get(incident.team, [1])
        
        localities = []
        for zone in incident.impacted_zones or []:
            localities.extend(ZONE_TO_LOCALITY.get(zone, [1]))
        if not localities:
            localities = [1]
        
        logger.info(f"Processing incident {incident.id} (team={incident.team}, zones={localities})")
        
        for org_id in org_ids:
            counters = call_get_filtered_counters(org_id, product_types, localities)
            matching_types = [rt for rt in resource_types if counters.get(rt, 0) > 0]
            
            if matching_types:
                alert = Alert(
def save_incidents_to_db(conn, incidents: List[Incident]):
    """Save incidents to database"""
    with conn.cursor() as cur:
        incident_data = [
            (
                i.id, i.severity, i.team, i.summary, i.impact,
                i.is_closed, i.start_time, i.end_time,
                Json(i.impacted_products), Json(i.impacted_zones),
                Json(i.comms_channel), i.report, i.ticket,
                Json({}), Json({})
            )
            for i in incidents
        ]
        
        execute_values(
            cur,
            """
            INSERT INTO incidents (incident_id, severity, team, summary, impact, is_closed, start_time, end_time, impacted_products, impacted_zones, comms_channel, report, ticket, lead, reporter)
            VALUES %s
            ON CONFLICT (incident_id) DO UPDATE SET severity = EXCLUDED.severity, team = EXCLUDED.team, summary = EXCLUDED.summary, impact = EXCLUDED.impact, is_closed = EXCLUDED.is_closed, end_time = EXCLUDED.end_time, updated_at = CURRENT_TIMESTAMP
            """,
            incident_data
        )
    
    conn.commit()
    logger.info(f"Saved {len(incidents)} incidents to database")


def save_alerts_to_db(conn, alerts: List[Alert]):
    """Save alerts to database with deduplication"""
    with conn.cursor() as cur:
        alert_data = [
            (a.incident_id, a.org_id, Json(a.resource_types), Json(a.localities), a.status)
            for a in alerts
        ]
        
        execute_values(
            cur,
            """
            INSERT INTO alerts (incident_id, org_id, resource_types, localities, status)
            VALUES %s
            ON CONFLICT (incident_id, org_id) DO UPDATE SET resource_types = EXCLUDED.resource_types, localities = EXCLUDED.localities, status = EXCLUDED.status, updated_at = CURRENT_TIMESTAMP
            """,
            alert_data
        )
    
    conn.commit()
    logger.info(f"Saved {len(alerts)} alerts to database")


def log_sync(conn, sync_type: str, status: str, records_processed: int, error_message: Optional[str] = None, duration_ms: int = 0):
    """Log sync execution"""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO sync_logs (sync_type, status, records_processed, error_message, duration_ms) VALUES (%s, %s, %s, %s, %s)",
            (sync_type, status, records_processed, error_message, duration_ms)
        )
    conn.commit()


def main():
    """Main entry point"""
    start_time = datetime.now(timezone.utc)
    logger.info("Starting match-incidents cron job")
    
    try:
        conn = get_db_connection()
        logger.info("Connected to database")
        
        incidents = fetch_incidents()
        if not incidents:
            logger.info("No open incidents found")
            log_sync(conn, 'match-incidents', 'success', 0, duration_ms=0)
            return
        
        save_incidents_to_db(conn, incidents)
        
        org_ids = get_organizations(conn)
        logger.info(f"Found {len(org_ids)} organizations")
        
        if not org_ids:
            logger.warning("No organizations found in database")
            log_sync(conn, 'match-incidents', 'warning', 0, error_message='No organizations found')
            return
        
        alerts = match_incidents_to_orgs(incidents, org_ids)
        save_alerts_to_db(conn, alerts)
        
        duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        log_sync(conn, 'match-incidents', 'success', len(alerts), duration_ms=duration_ms)
        
        logger.info(f"Completed successfully. Created {len(alerts)} alerts in {duration_ms}ms")
        
    except Exception as e:
        logger.error(f"Cron job failed: {e}", exc_info=True)
        try:
            conn = get_db_connection()
            log_sync(conn, 'match-incidents', 'error', 0, error_message=str(e))
        except:
            pass
        sys.exit(1)


if __name__ == '__main__':
    main()
                    incident_id=incident.id,
                    org_id=org_id,
                    resource_types=matching_types,
                    localities=localities
                )
                alerts.append(alert)
                logger.info(f"Created alert for org {org_id} on incident {incident.id}")
    
    return alerts
        return incidents
        
    except Exception as e:
        logger.error(f"Error fetching incidents: {e}")
        return []


def get_organizations(conn) -> List[str]:
    """Get all organization IDs from database"""
    with conn.cursor() as cur:
        cur.execute("SELECT org_id FROM organizations")
        return [row[0] for row in cur.fetchall()]
    'monitoring': [21],
    'iam': [9, 22, 23],
    'messaging': [20, 39],
    'webhosting': [25],
    'sre': [1, 2, 3, 5],
    'platform': [1, 9],
    'dedibox': [15, 25],
    'object-storage': [5],
    'cloud-compute': [1, 4, 8],
    'hardware': [8, 15],
}

ZONE_TO_LOCALITY: Dict[str, List[int]] = {
    'fr-par-1': [1],
    'fr-par-2': [2],
    'nl-ams-1': [3],
    'pl-waw-1': [4],
}