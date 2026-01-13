"""
Intent Handlers
===============
Whitelisted intent handlers that execute database operations.
All handlers use parameterized queries via db_client.

Security Notes:
- Only whitelisted intents are executed
- All database queries use parameterized statements
- Input validation happens before handlers are called
- Errors are caught and logged, never exposed to client
"""

from typing import Any, Dict, List, Optional
from db_client import get_db_client
from logger import get_logger
from validators import validate_limit, validate_timestamp, validate_ip_address, validate_status_code

logger = get_logger()


def handle_get_access_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve access logs with optional filters.
    
    Args:
        params: Query parameters (ip_address, status_code, start_time, end_time, limit)
        
    Returns:
        Dictionary with 'success' flag and 'data' or 'error'
    """
    try:
        db = get_db_client()
        
        # Build parameterized query
        conditions = []
        query_params = []
        
        # Optional filters
        if 'ip_address' in params and params['ip_address']:
            conditions.append('ip_address = %s')
            query_params.append(params['ip_address'])
        
        if 'status_code' in params and params['status_code']:
            conditions.append('status_code = %s')
            query_params.append(params['status_code'])
        
        if 'start_time' in params and params['start_time']:
            conditions.append('timestamp >= %s')
            query_params.append(params['start_time'])
        
        if 'end_time' in params and params['end_time']:
            conditions.append('timestamp <= %s')
            query_params.append(params['end_time'])
        
        if 'endpoint' in params and params['endpoint']:
            conditions.append('endpoint LIKE %s')
            query_params.append(f"%{params['endpoint']}%")
        
        # Build WHERE clause
        where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        
        # Get limit
        limit = params.get('limit', 100)
        is_valid, limit_val, _ = validate_limit(limit)
        if not is_valid:
            limit_val = 100
        
        # Execute query
        query = f"""
            SELECT 
                id, timestamp, ip_address, method, endpoint, 
                http_version, status_code, response_size, 
                response_time_ms, user_agent, department, user_id
            FROM access_logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT %s
        """
        query_params.append(limit_val)
        
        results = db.execute_query(query, tuple(query_params))
        
        return {
            'success': True,
            'data': {
                'logs': results,
                'count': len(results)
            }
        }
    
    except Exception as e:
        logger.error('Error in get_access_logs', error=e)
        return {
            'success': False,
            'error': 'Failed to retrieve access logs'
        }


def handle_get_error_logs(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve error logs with optional filters.
    
    Args:
        params: Query parameters (log_level, severity_score, start_time, end_time, limit)
        
    Returns:
        Dictionary with 'success' flag and 'data' or 'error'
    """
    try:
        db = get_db_client()
        
        conditions = []
        query_params = []
        
        if 'log_level' in params and params['log_level']:
            conditions.append('log_level = %s')
            query_params.append(params['log_level'])
        
        if 'severity_score' in params and params['severity_score']:
            conditions.append('severity_score >= %s')
            query_params.append(int(params['severity_score']))
        
        if 'start_time' in params and params['start_time']:
            conditions.append('timestamp >= %s')
            query_params.append(params['start_time'])
        
        if 'end_time' in params and params['end_time']:
            conditions.append('timestamp <= %s')
            query_params.append(params['end_time'])
        
        if 'error_code' in params and params['error_code']:
            conditions.append('error_code = %s')
            query_params.append(params['error_code'])
        
        where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        
        limit = params.get('limit', 100)
        is_valid, limit_val, _ = validate_limit(limit)
        if not is_valid:
            limit_val = 100
        
        query = f"""
            SELECT 
                id, timestamp, log_level, process_id, thread_id,
                client_ip, error_code, error_message, file_path,
                line_number, severity_score
            FROM error_logs
            {where_clause}
            ORDER BY timestamp DESC, severity_score DESC
            LIMIT %s
        """
        query_params.append(limit_val)
        
        results = db.execute_query(query, tuple(query_params))
        
        return {
            'success': True,
            'data': {
                'logs': results,
                'count': len(results)
            }
        }
    
    except Exception as e:
        logger.error('Error in get_error_logs', error=e)
        return {
            'success': False,
            'error': 'Failed to retrieve error logs'
        }


def handle_store_access_log(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store a new access log entry.
    
    Args:
        params: Access log fields (timestamp, ip_address, method, endpoint, etc.)
        
    Returns:
        Dictionary with 'success' flag and 'data' or 'error'
    """
    try:
        db = get_db_client()
        
        query = """
            INSERT INTO access_logs (
                timestamp, ip_address, method, endpoint, http_version,
                status_code, response_size, response_time_ms, user_agent,
                department, user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        query_params = (
            params['timestamp'],
            params['ip_address'],
            params['method'],
            params['endpoint'],
            params.get('http_version'),
            params['status_code'],
            params.get('response_size'),
            params.get('response_time_ms'),
            params.get('user_agent'),
            params.get('department'),
            params.get('user_id')
        )
        
        log_id = db.execute_insert(query, query_params)
        
        return {
            'success': True,
            'data': {
                'id': log_id,
                'message': 'Access log stored successfully'
            }
        }
    
    except Exception as e:
        logger.error('Error in store_access_log', error=e)
        return {
            'success': False,
            'error': 'Failed to store access log'
        }


def handle_store_error_log(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Store a new error log entry.
    
    Args:
        params: Error log fields (timestamp, log_level, error_code, error_message, etc.)
        
    Returns:
        Dictionary with 'success' flag and 'data' or 'error'
    """
    try:
        db = get_db_client()
        
        query = """
            INSERT INTO error_logs (
                timestamp, log_level, process_id, thread_id, client_ip,
                error_code, error_message, file_path, line_number, severity_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        query_params = (
            params['timestamp'],
            params['log_level'],
            params.get('process_id'),
            params.get('thread_id'),
            params.get('client_ip'),
            params['error_code'],
            params['error_message'],
            params.get('file_path'),
            params.get('line_number'),
            params.get('severity_score', 5)
        )
        
        log_id = db.execute_insert(query, query_params)
        
        return {
            'success': True,
            'data': {
                'id': log_id,
                'message': 'Error log stored successfully'
            }
        }
    
    except Exception as e:
        logger.error('Error in store_error_log', error=e)
        return {
            'success': False,
            'error': 'Failed to store error log'
        }


def handle_get_traffic_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get aggregated traffic statistics.
    
    Args:
        params: Optional time range (start_time, end_time)
        
    Returns:
        Dictionary with traffic summary statistics
    """
    try:
        db = get_db_client()
        
        conditions = []
        query_params = []
        
        if 'start_time' in params and params['start_time']:
            conditions.append('timestamp >= %s')
            query_params.append(params['start_time'])
        
        if 'end_time' in params and params['end_time']:
            conditions.append('timestamp <= %s')
            query_params.append(params['end_time'])
        
        where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        
        # Total requests
        total_query = f"SELECT COUNT(*) as total FROM access_logs {where_clause}"
        total_result = db.execute_query(total_query, tuple(query_params))
        total_requests = total_result[0]['total'] if total_result else 0
        
        # Error rate
        error_query = f"""
            SELECT COUNT(*) as errors 
            FROM access_logs 
            {where_clause} {'AND' if conditions else 'WHERE'} status_code >= 400
        """
        error_result = db.execute_query(error_query, tuple(query_params))
        error_count = error_result[0]['errors'] if error_result else 0
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        # Top endpoints
        top_endpoints_query = f"""
            SELECT endpoint, COUNT(*) as count
            FROM access_logs
            {where_clause}
            GROUP BY endpoint
            ORDER BY count DESC
            LIMIT 10
        """
        top_endpoints = db.execute_query(top_endpoints_query, tuple(query_params))
        
        # Top IPs
        top_ips_query = f"""
            SELECT ip_address, COUNT(*) as count
            FROM access_logs
            {where_clause}
            GROUP BY ip_address
            ORDER BY count DESC
            LIMIT 10
        """
        top_ips = db.execute_query(top_ips_query, tuple(query_params))
        
        return {
            'success': True,
            'data': {
                'total_requests': total_requests,
                'error_count': error_count,
                'error_rate': round(error_rate, 2),
                'top_endpoints': {row['endpoint']: row['count'] for row in top_endpoints},
                'top_ips': {row['ip_address']: row['count'] for row in top_ips}
            }
        }
    
    except Exception as e:
        logger.error('Error in get_traffic_summary', error=e)
        return {
            'success': False,
            'error': 'Failed to retrieve traffic summary'
        }


def handle_get_security_threats(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect security threats from logs.
    
    Args:
        params: Optional time range (start_time, end_time)
        
    Returns:
        Dictionary with detected security threats
    """
    try:
        db = get_db_client()
        
        conditions = []
        query_params = []
        
        if 'start_time' in params and params['start_time']:
            conditions.append('timestamp >= %s')
            query_params.append(params['start_time'])
        
        if 'end_time' in params and params['end_time']:
            conditions.append('timestamp <= %s')
            query_params.append(params['end_time'])
        
        where_clause = 'WHERE ' + ' AND '.join(conditions) if conditions else ''
        
        threats = []
        
        # Brute force detection (multiple 401s from same IP)
        brute_force_query = f"""
            SELECT ip_address, COUNT(*) as failures
            FROM access_logs
            {where_clause} {'AND' if conditions else 'WHERE'} status_code = 401
            GROUP BY ip_address
            HAVING failures >= 3
        """
        brute_results = db.execute_query(brute_force_query, tuple(query_params))
        
        for row in brute_results:
            threats.append({
                'severity': 'HIGH',
                'type': 'Brute Force Attack',
                'details': f"{row['failures']} failed login attempts from IP {row['ip_address']}",
                'ip_address': row['ip_address'],
                'count': row['failures']
            })
        
        # SQL injection detection (suspicious user agents)
        sql_injection_query = f"""
            SELECT ip_address, user_agent, endpoint
            FROM access_logs
            {where_clause} {'AND' if conditions else 'WHERE'} 
            (user_agent LIKE %s OR user_agent LIKE %s)
        """
        sql_params = list(query_params) + ['%sqlmap%', '%curl%']
        sql_results = db.execute_query(sql_injection_query, tuple(sql_params))
        
        for row in sql_results:
            threats.append({
                'severity': 'MEDIUM',
                'type': 'SQL Injection Attempt',
                'details': f"Suspicious tool detected: {row['user_agent']} from {row['ip_address']}",
                'ip_address': row['ip_address'],
                'endpoint': row['endpoint']
            })
        
        return {
            'success': True,
            'data': {
                'threats': threats,
                'count': len(threats)
            }
        }
    
    except Exception as e:
        logger.error('Error in get_security_threats', error=e)
        return {
            'success': False,
            'error': 'Failed to detect security threats'
        }


def handle_get_performance_metrics(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get performance metrics (slow endpoints).
    
    Args:
        params: Optional time range and threshold (start_time, end_time, threshold_ms)
        
    Returns:
        Dictionary with performance metrics
    """
    try:
        db = get_db_client()
        
        conditions = []
        query_params = []
        
        if 'start_time' in params and params['start_time']:
            conditions.append('timestamp >= %s')
            query_params.append(params['start_time'])
        
        if 'end_time' in params and params['end_time']:
            conditions.append('timestamp <= %s')
            query_params.append(params['end_time'])
        
        threshold = params.get('threshold_ms', 1000)
        conditions.append('response_time_ms > %s')
        query_params.append(threshold)
        
        where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f"""
            SELECT 
                endpoint,
                AVG(response_time_ms) as avg_response_time,
                MAX(response_time_ms) as peak_response_time,
                COUNT(*) as request_count
            FROM access_logs
            {where_clause}
            GROUP BY endpoint
            ORDER BY peak_response_time DESC
            LIMIT 20
        """
        
        results = db.execute_query(query, tuple(query_params))
        
        issues = []
        for row in results:
            issues.append({
                'endpoint': row['endpoint'],
                'avg_response_time_ms': round(row['avg_response_time'], 2),
                'peak_response_time_ms': row['peak_response_time'],
                'request_count': row['request_count'],
                'severity': 'HIGH' if row['peak_response_time'] > 3000 else 'MEDIUM'
            })
        
        return {
            'success': True,
            'data': {
                'issues': issues,
                'count': len(issues)
            }
        }
    
    except Exception as e:
        logger.error('Error in get_performance_metrics', error=e)
        return {
            'success': False,
            'error': 'Failed to retrieve performance metrics'
        }


def handle_get_anomalies(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect anomalies from error logs.
    
    Args:
        params: Optional filters (start_time, end_time, min_severity)
        
    Returns:
        Dictionary with detected anomalies
    """
    try:
        db = get_db_client()
        
        conditions = []
        query_params = []
        
        if 'start_time' in params and params['start_time']:
            conditions.append('timestamp >= %s')
            query_params.append(params['start_time'])
        
        if 'end_time' in params and params['end_time']:
            conditions.append('timestamp <= %s')
            query_params.append(params['end_time'])
        
        min_severity = params.get('min_severity', 8)
        conditions.append('severity_score >= %s')
        query_params.append(min_severity)
        
        where_clause = 'WHERE ' + ' AND '.join(conditions)
        
        query = f"""
            SELECT 
                timestamp, error_code, error_message, severity_score,
                client_ip, file_path
            FROM error_logs
            {where_clause}
            ORDER BY severity_score DESC, timestamp DESC
            LIMIT 50
        """
        
        results = db.execute_query(query, tuple(query_params))
        
        anomalies = []
        for row in results:
            anomalies.append({
                'timestamp': str(row['timestamp']),
                'error_code': row['error_code'],
                'error_message': row['error_message'],
                'severity_score': row['severity_score'],
                'severity': 'CRITICAL' if row['severity_score'] >= 9 else 'HIGH',
                'client_ip': row['client_ip'],
                'file_path': row['file_path']
            })
        
        return {
            'success': True,
            'data': {
                'anomalies': anomalies,
                'count': len(anomalies)
            }
        }
    
    except Exception as e:
        logger.error('Error in get_anomalies', error=e)
        return {
            'success': False,
            'error': 'Failed to detect anomalies'
        }


# Intent router mapping
INTENT_HANDLERS = {
    'get_access_logs': handle_get_access_logs,
    'get_error_logs': handle_get_error_logs,
    'store_access_log': handle_store_access_log,
    'store_error_log': handle_store_error_log,
    'get_traffic_summary': handle_get_traffic_summary,
    'get_security_threats': handle_get_security_threats,
    'get_performance_metrics': handle_get_performance_metrics,
    'get_anomalies': handle_get_anomalies,
}


def execute_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute intent handler.
    
    Args:
        intent: Intent name (must be whitelisted)
        params: Intent parameters
        
    Returns:
        Result dictionary from intent handler
    """
    handler = INTENT_HANDLERS.get(intent)
    
    if not handler:
        return {
            'success': False,
            'error': f'No handler for intent: {intent}'
        }
    
    return handler(params)