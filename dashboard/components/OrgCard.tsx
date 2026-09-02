import React from 'react';

interface OrgCardProps {
  orgId: string;
  name: string;
  activeAlertsCount: number;
  highestSeverity: string | null;
  distinctIncidents: number;
  onClick?: () => void;
}

const severityColors: Record<string, string> = {
  '1': 'bg-red-500',
  '2': 'bg-orange-500',
  '3': 'bg-yellow-500',
  '4': 'bg-blue-500',
};

const severityLabels: Record<string, string> = {
  '1': 'Critical',
  '2': 'High',
  '3': 'Medium',
  '4': 'Low',
};

export function OrgCard({ orgId, name, activeAlertsCount, highestSeverity, distinctIncidents, onClick }: OrgCardProps) {
  const severityColor = highestSeverity ? severityColors[highestSeverity] || 'bg-gray-500' : 'bg-green-500';
  const severityLabel = highestSeverity ? severityLabels[highestSeverity] || 'Unknown' : 'No Alerts';

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow-md p-6 cursor-pointer hover:shadow-lg transition-shadow border-l-4"
      style={{ borderLeftColor: highestSeverity ? severityColor.replace('bg-', '') : '#22c55e' }}
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold text-gray-900 truncate">{name}</h3>
        <span className={`px-2 py-1 rounded text-xs font-medium text-white ${severityColor}`}>
          {severityLabel}
        </span>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Active Alerts:</span>
          <span className={`font-medium ${activeAlertsCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
            {activeAlertsCount}
          </span>
        </div>
        
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Distinct Incidents:</span>
          <span className="font-medium text-gray-900">{distinctIncidents}</span>
        </div>
      </div>
      
      {activeAlertsCount > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            View Details →
          </button>
        </div>
      )}
    </div>
  );
}