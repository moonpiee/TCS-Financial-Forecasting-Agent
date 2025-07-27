import json
import mysql.connector
import os
import logging
from datetime import datetime, timezone
from mysql.connector import Error, pooling

logger = logging.getLogger(__name__)

try:
    dbconfig = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "pool_name": "mypool",
        "pool_size": 5,
    }
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(**dbconfig)
except Error as err:
    logger.error(f"Error creating connection pool: {err}")
    connection_pool = None

def log_request_response(request_id: str, request_data: dict, response_data: dict):
    if connection_pool is None:
        logger.error("No database connection pool available.")
        return

    try:
        conn = connection_pool.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forecast_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id VARCHAR(255) NOT NULL,
                request_data TEXT NOT NULL,
                response_data TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        cursor.execute("""
            INSERT INTO forecast_logs (request_id, request_data, response_data, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (
            request_id,
            json.dumps(request_data),
            json.dumps(response_data),
            datetime.now(timezone.utc)
        ))
        conn.commit()

        cursor.execute("SELECT * FROM forecast_logs WHERE request_id = %s", (request_id,))
        result = cursor.fetchall()
        logger.info(f"Logged record with request_id {request_id}: {result}")

    except Error as err:
        logger.error(f"Database error while logging request/response: {err}")

    except Exception as e:
        logger.error(f"Unexpected error in log_request_response: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def fetch_recent_logs(limit=20):
    if connection_pool is None:
        logger.error("No database connection pool available.")
        return []
    try:
        conn = connection_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT timestamp, request_data, response_data FROM forecast_logs ORDER BY timestamp DESC LIMIT %s", (limit,)
        )
        logs = cursor.fetchall()
        return logs
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
