# System Compromise - Xyrathian Orbital Surveillance Network

Flask-based web challenge featuring business logic vulnerabilities in a mission control system.

## Prerequisites

- Docker
- docker-compose

## Quick Start

1. Build the container:
   ```bash
   docker-compose build
   ```

2. Run the challenge:
   ```bash
   docker-compose up -d
   ```

3. Access the application:
   ```
   http://localhost:8082
   ```

4. Stop the challenge:
   ```bash
   docker-compose down
   ```

## Manual Setup (without Docker)

If running locally without Docker:

1. Install Python 3.11+

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize database:
   ```bash
   python database.py
   ```

4. Run application:
   ```bash
   python app.py
   ```

5. Access at `http://localhost:5000`

## Architecture

- **Backend**: Flask (Python 3.11)
- **Database**: SQLite (auto-initialized)
- **Port**: 5000 (container) → 8082 (host)

## Files

- `app.py` - Main Flask application
- `database.py` - Database initialization and queries
- `config.py` - Configuration and flags
- `templates/` - Jinja2 HTML templates
- `static/` - CSS, JavaScript, and assets

## Troubleshooting

**Container won't start:**
- Check if port 8082 is already in use: `lsof -i :8082`
- View logs: `docker-compose logs`

**Database issues:**
- Database is recreated on container rebuild
- No persistent storage configured (by design)

**Permission errors:**
- Ensure Docker has proper permissions
- On Linux, may need to run with `sudo`

## Development

To rebuild after code changes:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```
