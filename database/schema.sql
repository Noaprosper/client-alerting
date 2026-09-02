-- Schema for Scaleway Client Alerting Dashboard
-- PostgreSQL database schema

-- Table: organizations
-- Stores client organization information
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: incidents
-- Stores incident data from Incident API
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL UNIQUE,
    severity VARCHAR(10) NOT NULL,
    team VARCHAR(100) NOT NULL,
    summary TEXT NOT NULL,
    impact TEXT,
    is_closed BOOLEAN DEFAULT FALSE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    impacted_products JSONB,
    impacted_zones JSONB,
    comms_channel JSONB,
    report TEXT,
    ticket VARCHAR(100),
    lead JSONB,
    reporter JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: alerts
-- Stores alerts linking incidents to organizations
-- UNIQUE constraint ensures no duplicate alerts per incident+org
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES incidents(incident_id) ON DELETE CASCADE,
    org_id VARCHAR(255) NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    resource_types JSONB NOT NULL,
    localities JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    notified_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(incident_id, org_id)
);

-- Table: sync_logs
-- Stores cron job execution logs
CREATE TABLE IF NOT EXISTS sync_logs (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER
);

-- Index for faster alert queries
CREATE INDEX IF NOT EXISTS idx_alerts_org_id ON alerts(org_id);
CREATE INDEX IF NOT EXISTS idx_alerts_incident_id ON alerts(incident_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_incidents_is_closed ON incidents(is_closed);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);

-- View: v_active_alerts
-- Provides a convenient view of all active alerts with incident and org details
CREATE OR REPLACE VIEW v_active_alerts AS
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
WHERE a.status = 'active' AND i.is_closed = FALSE;

-- View: v_org_alert_summary
-- Provides summary stats per organization
CREATE OR REPLACE VIEW v_org_alert_summary AS
SELECT 
    o.org_id,
    o.name,
    COUNT(a.id) AS active_alerts_count,
    MAX(i.severity) AS highest_severity,
    COUNT(DISTINCT a.incident_id) AS distinct_incidents
FROM organizations o
LEFT JOIN alerts a ON o.org_id = a.org_id AND a.status = 'active'
LEFT JOIN incidents i ON a.incident_id = i.incident_id AND i.is_closed = FALSE
GROUP BY o.org_id, o.name;