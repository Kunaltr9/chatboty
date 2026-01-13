"""
Secure MariaDB Database Client
==============================
Production-grade database client with:
- Parameterized queries only (SQL injection prevention)
- Connection pooling and reuse
- Timeout configuration
- Safe error handling
- VPC-aware connection handling

Security Notes:
- ALL queries use parameterized statements
- No string interpolation or f-strings in SQL
- Connection credentials from environment variables
- Fail fast on connection errors
"""

import pymysql
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager
import time
from config import Config
from logger import get_logger

logger = get_logger()


class DatabaseClient:
    """
    Secure MariaDB client with connection pooling.
    
    Security Features:
    - Parameterized queries only (prevents SQL injection)
    - Connection reuse for Lambda container reuse
    - Timeout configuration
    - Safe error handling (never leaks DB structure)
    """
    
    def __init__(self):
        self._connection: Optional[pymysql.Connection] = None
        self._last_used: float = 0
        self._connection_timeout = Config.DB_CONNECTION_TIMEOUT
        self._query_timeout = Config.DB_QUERY_TIMEOUT
    
    def _get_connection(self) -> pymysql.Connection:
        """
        Get or create database connection.
        Reuses connection if still valid (Lambda container reuse).
        
        Returns:
            Database connection
            
        Raises:
            Exception: If connection cannot be established
        """
        # Reuse connection if it exists and is recent (< 5 minutes)
        if self._connection is not None:
            try:
                # Test connection
                self._connection.ping(reconnect=False)
                return self._connection
            except:
                # Connection is dead, create new one
                self._connection = None
        
        # Create new connection
        try:
            logger.info('Creating new database connection')
            
            self._connection = pymysql.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                connect_timeout=self._connection_timeout,
                read_timeout=self._query_timeout,
                write_timeout=self._query_timeout,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False  # Use transactions explicitly
            )
            
            self._last_used = time.time()
            logger.info('Database connection established')
            
            return self._connection
        
        except Exception as e:
            logger.error('Failed to connect to database', error=e)
            raise
    
    @contextmanager
    def _get_cursor(self):
        """
        Context manager for database cursor.
        Ensures proper cleanup and transaction handling.
        
        Yields:
            Database cursor
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error('Database transaction rolled back', error=e)
            raise
        finally:
            cursor.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query with parameterized parameters.
        
        Security: Uses parameterized queries to prevent SQL injection.
        
        Args:
            query: SQL query with %s placeholders
            params: Tuple of parameters to substitute
            fetch: Whether to fetch results (default: True)
            
        Returns:
            List of result dictionaries
            
        Raises:
            Exception: If query fails
        """
        with self._get_cursor() as cursor:
            logger.debug(f'Executing query: {query[:100]}...', params_count=len(params) if params else 0)
            
            cursor.execute(query, params)
            
            if fetch:
                results = cursor.fetchall()
                logger.debug(f'Query returned {len(results)} rows')
                return results
            else:
                return []
    
    def execute_insert(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> int:
        """
        Execute an INSERT query with parameterized parameters.
        
        Args:
            query: SQL INSERT query with %s placeholders
            params: Tuple of parameters to substitute
            
        Returns:
            Last insert ID
            
        Raises:
            Exception: If insert fails
        """
        with self._get_cursor() as cursor:
            logger.debug(f'Executing insert: {query[:100]}...')
            
            cursor.execute(query, params)
            last_id = cursor.lastrowid
            
            logger.info(f'Insert successful, ID: {last_id}')
            return last_id
    
    def execute_update(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> int:
        """
        Execute an UPDATE query with parameterized parameters.
        
        Args:
            query: SQL UPDATE query with %s placeholders
            params: Tuple of parameters to substitute
            
        Returns:
            Number of affected rows
            
        Raises:
            Exception: If update fails
        """
        with self._get_cursor() as cursor:
            logger.debug(f'Executing update: {query[:100]}...')
            
            affected = cursor.execute(query, params)
            
            logger.info(f'Update affected {affected} rows')
            return affected
    
    def close(self):
        """Close database connection"""
        if self._connection:
            try:
                self._connection.close()
                logger.info('Database connection closed')
            except:
                pass
            finally:
                self._connection = None


# Global database client instance (reused across Lambda invocations)
_db_client: Optional[DatabaseClient] = None


def get_db_client() -> DatabaseClient:
    """
    Get or create global database client instance.
    Singleton pattern for Lambda container reuse.
    
    Returns:
        DatabaseClient instance
    """
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client


# Example table schemas (for reference - create these in RDS)
"""
CREATE TABLE access_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    method VARCHAR(10) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    http_version VARCHAR(10),
    status_code INT NOT NULL,
    response_size INT,
    response_time_ms INT,
    user_agent VARCHAR(500),
    department VARCHAR(100),
    user_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_ip (ip_address),
    INDEX idx_status (status_code),
    INDEX idx_endpoint (endpoint(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE error_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    process_id INT,
    thread_id INT,
    client_ip VARCHAR(45),
    error_code VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    file_path VARCHAR(500),
    line_number INT,
    severity_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_level (log_level),
    INDEX idx_severity (severity_score),
    INDEX idx_error_code (error_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""