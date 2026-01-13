import React from 'react';

interface ThreatCardProps {
    severity: string;
    type: string;
    details: string;
    recommendation: string;
}

const ThreatCard: React.FC<ThreatCardProps> = ({ severity, type, details, recommendation }) => {
    const severityColors = {
        HIGH: 'bg-red-600',
        MEDIUM: 'bg-yellow-500',
        LOW: 'bg-blue-500',
        CRITICAL: 'bg-purple-700',
    };

    return (
        <div className={`p-4 rounded-lg shadow-lg ${severityColors[severity] || 'bg-gray-800'} text-white`}>
            <h3 className="text-xl font-bold">{type}</h3>
            <p className="mt-2">{details}</p>
            <p className="mt-4 font-semibold">Recommendation:</p>
            <p>{recommendation}</p>
        </div>
    );
};

export default ThreatCard;