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
  }
]

export default mockSecurityEvents
