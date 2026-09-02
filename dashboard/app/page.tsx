'use client';

import React, { useState, useEffect } from 'react';
import { OrgCard } from '../components/OrgCard';
import { SummaryStats } from '../components/SummaryStats';

interface OrgAlertSummary {
  org_id: string;
  name: string;
  active_alerts_count: number;
  highest_severity: string | null;
  distinct_incidents: number;
}

interface Alert {
  alert_id: number;
  org_id: string;
  org_name: string;
  incident_id: number;
  severity: string;
  team: string;
  summary: string;
  start_time: string;
  status: string;
}

export default function Dashboard() {
  const [orgs, setOrgs] = useState<OrgAlertSummary[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrg, setSelectedOrg] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [lastSync, setLastSync] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [orgsRes, alertsRes] = await Promise.all([fetch('/api/orgs'), fetch('/api/alerts')]);
      if (orgsRes.ok) setOrgs(await orgsRes.json());
      if (alertsRes.ok) setAlerts(await alertsRes.json());
      setLastSync(new Date().toISOString());
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredOrgs = orgs.filter(org => filterSeverity === 'all' || org.highest_severity === filterSeverity);
  const filteredAlerts = alerts.filter(alert => {
    if (selectedOrg && alert.org_id !== selectedOrg) return false;
    if (filterSeverity !== 'all' && alert.severity !== filterSeverity) return false;
    return true;
  });

  if (loading) return <div className="min-h-screen bg-gray-50 flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div></div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Scaleway Client Alerting Dashboard</h1>
        <p className="text-gray-600 mb-6">Monitor active incident alerts across all clients</p>
        <SummaryStats totalOrgs={orgs.length} activeAlerts={alerts.length} openIncidents={new Set(alerts.map(a => a.incident_id)).size} lastSync={lastSync} />
        <div className="mb-6">
          <select value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)} className="px-4 py-2 border rounded-md bg-white">
            <option value="all">All Severities</option>
            <option value="1">Critical</option>
            <option value="2">High</option>
            <option value="3">Medium</option>
            <option value="4">Low</option>
          </select>
        </div>
        <section className="mb-12">
          <h2 className="text-xl font-semibold mb-4">Organizations ({filteredOrgs.length})</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {filteredOrgs.map(org => (<OrgCard key={org.org_id} orgId={org.org_id} name={org.name} activeAlertsCount={org.active_alerts_count} highestSeverity={org.highest_severity} distinctIncidents={org.distinct_incidents} onClick={() => setSelectedOrg(selectedOrg === org.org_id ? null : org.org_id)} />))}
          </div>
        </section>
        {filteredAlerts.length > 0 && (
          <section>
            <h2 className="text-xl font-semibold mb-4">Active Alerts ({filteredAlerts.length})</h2>
            <div className="bg-white rounded shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Org</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Summary</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Team</th><th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Started</th></tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredAlerts.map(alert => (
                    <tr key={alert.alert_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium">{alert.org_name}</td>
                      <td className="px-6 py-4"><span className={`px-2 py-1 text-xs rounded text-white ${alert.severity==='1'?'bg-red-500':alert.severity==='2'?'bg-orange-500':alert.severity==='3'?'bg-yellow-500':'bg-blue-500'}`}>{alert.severity}</span></td>
                      <td className="px-6 py-4 text-sm truncate max-w-md">{alert.summary}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">{alert.team}</td>
                      <td className="px-6 py-4 text-sm text-gray-500">{new Date(alert.start_time).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}