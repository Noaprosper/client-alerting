import React from 'react';

interface SummaryStatsProps {
  totalOrgs: number;
  activeAlerts: number;
  openIncidents: number;
  lastSync: string | null;
}

export function SummaryStats({ totalOrgs, activeAlerts, openIncidents, lastSync }: SummaryStatsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-sm text-gray-500 mb-1">Total Organizations</div>
        <div className="text-3xl font-bold text-gray-900">{totalOrgs}</div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-sm text-gray-500 mb-1">Active Alerts</div>
        <div className={`text-3xl font-bold ${activeAlerts > 0 ? 'text-red-600' : 'text-green-600'}`}>
          {activeAlerts}
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-sm text-gray-500 mb-1">Open Incidents</div>
        <div className={`text-3xl font-bold ${openIncidents > 0 ? 'text-orange-600' : 'text-green-600'}`}>
          {openIncidents}
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-sm text-gray-500 mb-1">Last Sync</div>
        <div className="text-lg font-medium text-gray-900">
          {lastSync ? new Date(lastSync).toLocaleString() : 'Never'}
        </div>
      </div>
    </div>
  );
}