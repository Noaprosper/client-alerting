import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export interface Alert {
  alert_id: number;
  org_id: string;
  org_name: string;
  incident_id: number;
  severity: string;
  team: string;
  summary: string;
  impact: string;
  start_time: string;
  ticket: string | null;
  resource_types: number[];
  localities: number[];
  status: string;
  alert_created_at: string;
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const orgId = searchParams.get('org_id');
    
    const client = await pool.connect();
    
    let query = `
      SELECT 
        a.id AS alert_id,
        a.org_id,
        o.name AS org_name,
        a.incident_id,
        i.severity,
        i.team,
        i.summary,
        i.impact,
        i.start_time,
        i.ticket,
        a.resource_types,
        a.localities,
        a.status,
        a.created_at AS alert_created_at
      FROM alerts a
      JOIN organizations o ON a.org_id = o.org_id
      JOIN incidents i ON a.incident_id = i.incident_id
      WHERE a.status = 'active' AND i.is_closed = FALSE
    `;
    
    const params: any[] = [];
    
    if (orgId) {
      params.push(orgId);
      query += ' AND a.org_id = $1';
    }
    
    query += ' ORDER BY i.severity ASC, a.created_at DESC';
    
    const result = await client.query(query, params);
    client.release();
    
    const alerts: Alert[] = result.rows.map(row => ({
      alert_id: row.alert_id,
      org_id: row.org_id,
      org_name: row.org_name,
      incident_id: row.incident_id,
      severity: row.severity,
      team: row.team,
      summary: row.summary,
      impact: row.impact,
      start_time: row.start_time,
      ticket: row.ticket,
      resource_types: row.resource_types || [],
      localities: row.localities || [],
      status: row.status,
      alert_created_at: row.alert_created_at,
    }));
    
    return NextResponse.json(alerts);
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch alerts' },
      { status: 500 }
    );
  }
}