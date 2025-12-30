"""
Xyrathian Orbital Surveillance Network - Mission Control Interface
Flask web application with intentional business logic vulnerabilities
"""
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import database
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Initialize database on first run
try:
    database.init_database()
except:
    pass  # Database already exists


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    """Field operator login - sets session"""
    # Simple login as field operator (user_id 1000)
    session['user_id'] = 1000
    session['username'] = 'Field Operator Vex\'rin'
    session['role'] = 'operator'
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    """Clear session"""
    session.clear()
    return redirect(url_for('index'))


# ============================================================================
# PAGE ROUTES
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """Main mission control dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # Get user's missions
    user_missions = database.get_user_missions(session['user_id'])
    
    return render_template('dashboard.html', 
                         username=session.get('username'),
                         role=session.get('role'),
                         missions=user_missions)


@app.route('/create-mission')
def create_mission_page():
    """Mission creation form"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('create_mission.html', 
                         target_zones=config.TARGET_ZONES)


@app.route('/mission/<int:mission_id>')
def mission_status_page(mission_id):
    """Mission details page"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    mission = database.get_mission(mission_id)
    if not mission:
        return "Mission not found", 404
    
    return render_template('mission_status.html', mission=mission)


@app.route('/fleet')
def fleet_page():
    """Drone fleet manifest page"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    drones = database.get_fleet()
    return render_template('fleet.html', drones=drones)


@app.route('/operations')
def operations_page():
    """Operations history page"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return render_template('operations.html')


@app.route('/feed/<int:mission_id>')
def feed_page(mission_id):
    """Surveillance feed viewer"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    mission = database.get_mission(mission_id)
    if not mission:
        return "Mission not found", 404
    
    if mission['status'] != 'active':
        return render_template('feed.html', 
                             mission=mission, 
                             error="Mission must be approved before accessing feed")
    
    # Check drone clearance level for Flag 6
    clearance_level = mission['clearance_level']
    has_crypto = clearance_level == 3
    
    return render_template('feed.html', 
                         mission=mission,
                         clearance_level=clearance_level,
                         clearance_type=config.CLEARANCE_LEVELS.get(clearance_level),
                         has_crypto=has_crypto,
                         flag=config.FLAG_6 if has_crypto else None)


# ============================================================================
# API ROUTES - Mission Management
# ============================================================================

@app.route('/api/mission/create', methods=['POST'])
def api_create_mission():
    """
    Create a new surveillance mission
    
    VULNERABLE: Accepts drone_id parameter without authorization check
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    target_zone = data.get('target_zone')
    duration_hours = data.get('duration_hours', 24)
    drone_id = data.get('drone_id')  # VULNERABLE: User can specify any drone!
    
    if not target_zone:
        return jsonify({'error': 'Missing target_zone'}), 400
    
    # Create mission (will use provided drone_id if given)
    mission_id = database.create_mission(
        user_id=session['user_id'],
        target_zone=target_zone,
        duration_hours=duration_hours,
        drone_id=drone_id
    )
    
    if mission_id is None:
        return jsonify({'error': 'Invalid drone_id - drone does not exist'}), 404
    
    # Get created mission details
    mission = database.get_mission(mission_id)
    
    return jsonify({
        'success': True,
        'mission_id': mission_id,
        'target_zone': target_zone,
        'duration_hours': duration_hours,
        'assigned_drone_id': mission['assigned_drone_id'],
        'status': mission['status']
    })


@app.route('/api/mission/status/<int:mission_id>')
def api_mission_status(mission_id):
    """
    Get mission status with HATEOAS links
    
    Returns _links object that reveals available endpoints
    """
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    mission = database.get_mission(mission_id)
    if not mission:
        return jsonify({'error': 'Mission not found'}), 404
    
    # Build HATEOAS-style response with discoverable links
    response = {
        'mission_id': mission['mission_id'],
        'user_id': mission['user_id'],
        'target_zone': mission['target_zone'],
        'duration_hours': mission['duration_hours'],
        'status': mission['status'],
        'assigned_drone_id': mission['assigned_drone_id'],
        'drone_details': {
            'id': mission['assigned_drone_id'],
            'clearance_type': config.CLEARANCE_LEVELS.get(mission['clearance_level']),
            'equipment': mission['equipment'],
            'operational': mission['drone_status'] == 'active'
        },
        '_links': {
            'self': f'/api/mission/status/{mission_id}',
            'approve': '/api/mission/approve',
            'cancel': f'/api/mission/cancel/{mission_id}',
            'feed': f'/feed/{mission_id}'
        }
    }
    
    # FLAG 5: Show flag if mission was approved (active status)
    if mission['status'] == 'active':
        response['flag'] = config.FLAG_5
    
    return jsonify(response)


# ============================================================================
# VULNERABLE ROUTES - Intentional Security Flaws
# ============================================================================

@app.route('/api/mission/approve', methods=['POST'])
def api_approve_mission():
    """
    Approve a mission - FLAG 5 VULNERABILITY
    
    CRITICAL FLAW: No authorization check!
    Any user can approve any mission without commander role
    """
    data = request.get_json()
    mission_id = data.get('mission_id')
    
    if not mission_id:
        return jsonify({'error': 'Missing mission_id'}), 400
    
    # VULNERABILITY: Should check if user has commander role, but doesn't!
    # if session.get('role') != 'commander':
    #     return jsonify({'error': 'Unauthorized'}), 403
    
    success = database.approve_mission(mission_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Mission approved',
            'mission_id': mission_id,
            'flag': config.FLAG_5  # Flag revealed on successful exploit
        })
    
    return jsonify({'error': 'Mission not found'}), 404


# ============================================================================
# SUPPORTING API ROUTES
# ============================================================================

@app.route('/api/mission/history')
def api_mission_history():
    """Get recent mission history across all users"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    history = database.get_mission_history()
    
    # Format for display
    missions = []
    for mission in history:
        missions.append({
            'mission_id': mission['mission_id'],
            'user': mission['username'],
            'drone_id': mission['assigned_drone_id'],
            'target': mission['target_zone'].replace('_', ' ').title(),
            'status': mission['status']
        })
    
    return jsonify({'missions': missions})


@app.route('/api/fleet/list')
def api_fleet_list():
    """Get complete drone fleet information"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    drones = database.get_fleet()
    
    # Format for API response
    drone_list = []
    for drone in drones:
        drone_list.append({
            'drone_id': drone['drone_id'],
            'status': drone['status'],
            'clearance_level': drone['clearance_level'],
            'clearance_type': config.CLEARANCE_LEVELS.get(drone['clearance_level']),
            'equipment': drone['equipment']
        })
    
    return jsonify({'drones': drone_list})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
