"""
Database module for storing and retrieving history records
Uses SQLite for simplicity and portability
"""
import aiosqlite
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')


async def init_db():
    """
    Initialize the database and create tables if they don't exist
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # History table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sheet_name TEXT NOT NULL,
                step TEXT,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                time TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE INDEX IF NOT EXISTS idx_sheet_name ON history(sheet_name)
        ''')
        await db.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON history(timestamp)
        ''')
        
        # Active processes table (shared Monitor)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS active_processes (
                process_id TEXT PRIMARY KEY,
                step_name TEXT NOT NULL,
                sheet_name TEXT NOT NULL,
                session_id TEXT NOT NULL,
                stats TEXT NOT NULL,
                elapsed_time INTEGER DEFAULT 0,
                is_completed INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                progress REAL DEFAULT 0,
                start_time INTEGER NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.execute('''
            CREATE INDEX IF NOT EXISTS idx_active_processes_sheet ON active_processes(sheet_name)
        ''')
        await db.execute('''
            CREATE INDEX IF NOT EXISTS idx_active_processes_active ON active_processes(is_active)
        ''')
        
        await db.commit()
        logger.info("Database initialized successfully")


async def save_history(sheet_name: str, step: Optional[str], message: str, timestamp: str, time: str) -> int:
    """
    Save a history record to the database
    
    Args:
        sheet_name: Name of the sheet
        step: Step name (optional)
        message: History message
        timestamp: ISO timestamp string
        time: Local time string
        
    Returns:
        ID of the inserted record
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                INSERT INTO history (sheet_name, step, message, timestamp, time)
                VALUES (?, ?, ?, ?, ?)
            ''', (sheet_name, step, message, timestamp, time))
            await db.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error saving history: {e}")
        raise


async def get_history(limit: int = 100, sheet_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve history records from the database
    
    Args:
        limit: Maximum number of records to return
        sheet_name: Optional filter by sheet name
        
    Returns:
        List of history records as dictionaries
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row  # Return rows as dictionaries
            
            if sheet_name:
                cursor = await db.execute('''
                    SELECT id, sheet_name, step, message, timestamp, time, created_at
                    FROM history
                    WHERE sheet_name = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (sheet_name, limit))
            else:
                cursor = await db.execute('''
                    SELECT id, sheet_name, step, message, timestamp, time, created_at
                    FROM history
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise


async def get_history_by_sheet() -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve history records grouped by sheet name
    
    Returns:
        Dictionary with sheet names as keys and lists of history records as values
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute('''
                SELECT id, sheet_name, step, message, timestamp, time, created_at
                FROM history
                ORDER BY timestamp DESC
            ''')
            
            rows = await cursor.fetchall()
            records = [dict(row) for row in rows]
            
            # Group by sheet name
            grouped = {}
            for record in records:
                sheet = record['sheet_name']
                if sheet not in grouped:
                    grouped[sheet] = []
                grouped[sheet].append(record)
            
            return grouped
    except Exception as e:
        logger.error(f"Error retrieving grouped history: {e}")
        raise


async def clear_history():
    """
    Clear all history records (use with caution)
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('DELETE FROM history')
            await db.commit()
            logger.info("History cleared")
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise


async def save_or_update_process(
    process_id: str,
    step_name: str,
    sheet_name: str,
    session_id: str,
    stats: Dict[str, Any],
    elapsed_time: int,
    is_completed: bool,
    is_active: bool,
    progress: float,
    start_time: int
):
    """
    Save or update an active process in the database
    """
    import json
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            stats_json = json.dumps(stats)
            await db.execute('''
                INSERT INTO active_processes (
                    process_id, step_name, sheet_name, session_id, stats,
                    elapsed_time, is_completed, is_active, progress, start_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(process_id) DO UPDATE SET
                    step_name = EXCLUDED.step_name,
                    sheet_name = EXCLUDED.sheet_name,
                    session_id = EXCLUDED.session_id,
                    stats = EXCLUDED.stats,
                    elapsed_time = EXCLUDED.elapsed_time,
                    is_completed = EXCLUDED.is_completed,
                    is_active = EXCLUDED.is_active,
                    progress = EXCLUDED.progress,
                    start_time = EXCLUDED.start_time,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                process_id, step_name, sheet_name, session_id, stats_json,
                elapsed_time, 1 if is_completed else 0, 1 if is_active else 0, progress, start_time
            ))
            await db.commit()
            logger.debug(f"Process {process_id} saved/updated in DB")
    except Exception as e:
        logger.error(f"Error saving/updating process {process_id}: {e}")
        raise


async def get_active_processes() -> List[Dict[str, Any]]:
    """
    Get all active and recently completed processes from the database
    """
    import json
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            # Get processes that are active or completed within the last 24 hours
            cursor = await db.execute('''
                SELECT * FROM active_processes
                WHERE is_active = 1 OR (is_completed = 1 AND updated_at > datetime('now', '-24 hours'))
                ORDER BY start_time DESC
            ''')
            rows = await cursor.fetchall()
            processes = []
            for row in rows:
                process = dict(row)
                process['stats'] = json.loads(process['stats'])
                process['is_completed'] = bool(process['is_completed'])
                process['is_active'] = bool(process['is_active'])
                processes.append(process)
            return processes
    except Exception as e:
        logger.error(f"Error retrieving active processes: {e}")
        raise


async def delete_process(process_id: str):
    """
    Delete a process from the active_processes table
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('DELETE FROM active_processes WHERE process_id = ?', (process_id,))
            await db.commit()
            logger.debug(f"Process {process_id} deleted from DB")
    except Exception as e:
        logger.error(f"Error deleting process {process_id}: {e}")
        raise

