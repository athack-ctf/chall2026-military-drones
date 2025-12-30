"""
Configuration settings for the Xyrathian Orbital Surveillance Network
"""
import os

# Flask configuration
SECRET_KEY = os.environ.get('FLASK_SECRET', 'xyrathian_orbital_key_v2_beta')
DATABASE = 'surveillance.db'

# Flag values
FLAG_5 = 'ATHACKCTF{unauth0r1z3d_m1ss10n_4ppr0v4l}'
FLAG_6 = 'ATHACKCTF{3sc4l4t3d_surv31ll4nc3_4cc3ss}'

# Drone fleet configuration
DRONE_RANGES = {
    'classified': (1, 999),
    'military': (1000, 4999),
    'civilian': (5000, 9999)
}

# Available target zones for surveillance missions
TARGET_ZONES = [
    {'id': 'north_america_sector_7', 'name': 'North America - Sector 7'},
    {'id': 'europe_zone_12', 'name': 'Europe - Zone 12'},
    {'id': 'pacific_grid_5', 'name': 'Pacific Grid - Sector 5'},
    {'id': 'asian_network_3', 'name': 'Asian Network - Sector 3'},
    {'id': 'arctic_sector_classified', 'name': 'Arctic Sector - Classified'},
    {'id': 'facility_omega', 'name': 'Facility Omega'},
]

# Clearance level definitions
CLEARANCE_LEVELS = {
    1: 'CIVILIAN',
    2: 'MILITARY',
    3: 'CLASSIFIED'
}

# Equipment types by clearance
EQUIPMENT_TYPES = {
    1: 'Standard Optics',
    2: 'Enhanced Surveillance',
    3: 'Full Spectrum + Crypto'
}
