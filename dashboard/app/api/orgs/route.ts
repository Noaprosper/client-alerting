import { NextResponse } from 'next/server';
import { Pool } from 'pg';

// Database connection pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export interface OrgAlertSummary {
  org_id: string;
  name: string;
  active_alerts_count: number;
  highest_severity: string | null;
  distinct_incidents: number;
}

export async function GET() {
  try {
    const client = await pool.connect();
    
    // Get all organizations with their alert summaries
    const result = await client.query(`
      SELECT 
        o.org_id,
        o.name,
        COUNT(a.id) AS active_alerts_count,
        MAX(i.severity) AS highest_severity,
        COUNT(DISTINCT a.incident_id) AS distinct_incidents
      FROM organizations o
      LEFT JOIN alerts a ON o.org_id = a.org_id AND a.status = 'active'
      LEFT JOIN incidents i ON a.incident_id = i.incident_id AND i.is_closed = FALSE
      GROUP BY o.org_id, o.name
      ORDER BY 
        CASE MAX(i.severity)
          WHEN '1' THEN 1
          WHEN '2' THEN 2
          WHEN '3' THEN 3
          WHEN '4' THEN 4
          ELSE 5
        END,
        active_alerts_count DESC
    `);
    
    client.release();
    
    const orgs: OrgAlertSummary[] = result.rows.map(row => ({
      org_id: row.org_id,
      name: row.name,
      active_alerts_count: parseInt(row.active_alerts_count),
      highest_severity: row.highest_severity,
      distinct_incidents: parseInt(row.distinct_incidents),
    }));
    
    return NextResponse.json(orgs);
  } catch (error) {
    console.error('Error fetching organizations:', error);
    return NextResponse.json(
      { error: 'Failed to fetch organizations' },
      { status: 500 }
    );
  }
}