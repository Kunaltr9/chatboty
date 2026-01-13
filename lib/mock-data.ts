export const mockSecurityEvents = [
  {
    id: 'evt-1001',
    severity: 'High',
    type: 'Unauthorized Access Attempt',
    source: '10.0.0.12',
    timestamp: '2026-01-12T08:12:34Z',
    details: 'Multiple failed authentication attempts detected for user admin.',
    status: 'Open'
  },
  {
    id: 'evt-1002',
    severity: 'Medium',
    type: 'Suspicious Activity',
    source: '172.16.5.4',
    timestamp: '2026-01-12T07:58:01Z',
    details: 'Unrecognized user agent seen performing POST requests to /login.',
    status: 'Investigating'
  },
  {
    id: 'evt-1003',
    severity: 'Low',
    type: 'Anomalous Traffic Spike',
    source: '192.168.1.200',
    timestamp: '2026-01-11T23:45:12Z',
    details: 'Short-lived increase in requests to /api/data from a single IP.',
    status: 'Closed'
  }
];

export default mockSecurityEvents;
