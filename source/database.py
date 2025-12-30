"""
Database management for the Xyrathian Orbital Surveillance Network
"""
import sqlite3
import random
from datetime import datetime, timedelta
from config import DATABASE, DRONE_RANGES, CLEARANCE_LEVELS, EQUIPMENT_TYPES


def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database with schema and seed data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drones (
            drone_id INTEGER PRIMARY KEY,
            status TEXT NOT NULL,
            clearance_level INTEGER NOT NULL,
            equipment TEXT NOT NULL,
            last_location TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS missions (
            mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            target_zone TEXT NOT NULL,
            duration_hours INTEGER NOT NULL,
            status TEXT NOT NULL,
            assigned_drone_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (assigned_drone_id) REFERENCES drones(drone_id)
        )
    ''')
    
    # Seed users
    users_data = [
        (1000, 'Field Operator Vex\'rin', 'operator'),
        (2000, 'Commander Thon\'var', 'commander'),
        (1001, 'Operator Zix\'val', 'operator'),
        (1002, 'Operator Krel\'mok', 'operator'),
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO users (user_id, username, role) VALUES (?, ?, ?)', users_data)
    
    # Seed drones
    drones_data = []
    
    # Classified drones (1-999): Full Spectrum + Crypto, clearance level 3
    # Use low IDs (< 100) to make pattern obvious for beginners
    classified_ids = [12, 23, 34, 42, 56, 67, 78, 89, 91, 95]
    for drone_id in classified_ids:
        drones_data.append((
            drone_id,
            'active',
            3,
            EQUIPMENT_TYPES[3],
            None
        ))
    
    # Military drones (1000-4999): Enhanced Surveillance, clearance level 2
    military_ids = [1205, 1847, 2341, 3092, 3847, 4201]
    for drone_id in military_ids:
        drones_data.append((
            drone_id,
            'active',
            2,
            EQUIPMENT_TYPES[2],
            None
        ))
    
    # Civilian drones (5000-9999): Standard Optics, clearance level 1
    civilian_ids = [5234, 5847, 6012, 6543, 7234, 7891, 8102, 8567, 9123, 9456]
    for drone_id in civilian_ids:
        drones_data.append((
            drone_id,
            'active',
            1,
            EQUIPMENT_TYPES[1],
            None
        ))
    
    cursor.executemany('INSERT OR IGNORE INTO drones (drone_id, status, clearance_level, equipment, last_location) VALUES (?, ?, ?, ?, ?)', drones_data)
    
    # Seed historical missions to show pattern
    # Operators get civilian drones (5000+ = four-digit), commanders get classified (< 100 = two-digit)
    # This creates obvious visual pattern for beginners: commanders = two-digit, operators = four-digit
    historical_missions = [
        (1001, 'europe_zone_12', 24, 'completed', 7891, datetime.now() - timedelta(days=5)),
        (2000, 'asian_network_3', 48, 'completed', 67, datetime.now() - timedelta(days=4)),
        (1002, 'pacific_grid_5', 24, 'completed', 5234, datetime.now() - timedelta(days=3)),
        (2000, 'arctic_sector_classified', 72, 'active', 56, datetime.now() - timedelta(days=2)),
        (1001, 'north_america_sector_7', 24, 'completed', 8102, datetime.now() - timedelta(days=1)),
        (2000, 'europe_zone_12', 36, 'completed', 42, datetime.now() - timedelta(hours=18)),
        (1002, 'pacific_grid_5', 24, 'completed', 6543, datetime.now() - timedelta(hours=12)),
    ]
    
    for mission in historical_missions:
        cursor.execute('''
            INSERT OR IGNORE INTO missions (user_id, target_zone, duration_hours, status, assigned_drone_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', mission)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")


def create_mission(user_id, target_zone, duration_hours, drone_id=None):
    """
    Create a new surveillance mission
    
    If drone_id is provided, use it (VULNERABLE - no authorization check!)
    Otherwise, assign a random civilian drone
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if drone_id is None:
        # Assign random civilian drone by default
        cursor.execute('SELECT drone_id FROM drones WHERE clearance_level = 1 AND status = "active"')
        civilian_drones = [row['drone_id'] for row in cursor.fetchall()]
        drone_id = random.choice(civilian_drones) if civilian_drones else 5847
    else:
        # If user specified a drone_id, check if it exists
        cursor.execute('SELECT drone_id FROM drones WHERE drone_id = ?', (drone_id,))
        if not cursor.fetchone():
            conn.close()
            return None  # Drone doesn't exist
    
    cursor.execute('''
        INSERT INTO missions (user_id, target_zone, duration_hours, status, assigned_drone_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, target_zone, duration_hours, 'pending', drone_id))
    
    mission_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return mission_id


def get_mission(mission_id):
    """Get mission details with drone information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, d.status as drone_status, d.clearance_level, d.equipment
        FROM missions m
        LEFT JOIN drones d ON m.assigned_drone_id = d.drone_id
        WHERE m.mission_id = ?
    ''', (mission_id,))
    
    mission = cursor.fetchone()
    conn.close()
    
    if mission:
        return dict(mission)
    return None


def approve_mission(mission_id):
    """
    Approve a mission (VULNERABLE - no authorization check!)
    
    This should require commander role but doesn't check
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE missions SET status = ? WHERE mission_id = ?', ('active', mission_id))
    conn.commit()
    
    success = cursor.rowcount > 0
    conn.close()
    
    return success


def get_fleet():
    """Get complete drone fleet manifest"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM drones ORDER BY drone_id ASC')
    drones = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return drones


def get_mission_history():
    """Get recent mission history across all users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.mission_id, m.target_zone, m.status, m.assigned_drone_id, 
               u.username, m.created_at
        FROM missions m
        JOIN users u ON m.user_id = u.user_id
        ORDER BY m.created_at DESC
        LIMIT 10
    ''')
    
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return history


def get_user_missions(user_id):
    """Get all missions for a specific user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, d.clearance_level, d.equipment
        FROM missions m
        JOIN drones d ON m.assigned_drone_id = d.drone_id
        WHERE m.user_id = ?
        ORDER BY m.created_at DESC
    ''', (user_id,))
    
    missions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return missions


if __name__ == '__main__':
    # Initialize database when run directly
    init_database()
