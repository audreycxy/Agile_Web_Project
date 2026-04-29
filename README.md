# Agile Web Project - Clicking Game

A Flask clicking-game web app with role-based login, SQLAlchemy ORM models, Alembic migrations, SQLite persistence, and Docker support.

## Current Structure

```text
.
|-- Clicking_Game/
|   |-- __init__.py              # Flask app factory and configuration
|   |-- app.py                   # Local development entry point
|   |-- models/
|   |   |-- database.py          # SQLAlchemy engine/session and Alembic commands
|   |   `-- users.py             # User and game-result ORM models
|   |-- routes/
|   |   |-- auth.py              # Login, signup, logout, dashboards
|   |   `-- main.py              # Home and guest pages
|   |-- static/
|   `-- templates/
|-- migrations/
|   |-- env.py                   # Alembic migration environment
|   |-- script.py.mako           # Alembic revision template
|   `-- versions/
|       `-- 0001_create_initial_tables.py
|-- scripts/
|   |-- add_user.py              # Add one user to app.db
|   `-- seed_users.py            # Add starter users to app.db
|-- alembic.ini
|-- docker-compose.yml
|-- Dockerfile
|-- requirements.txt
`-- wsgi.py                      # WSGI server entry point
```

## Database

The app uses SQLAlchemy ORM models and Alembic migrations. The SQLite database file is named `app.db`.

Default local database path:

```text
instance/app.db
```

Default Docker database path inside the container:

```text
/app/instance/app.db
```

The schema is defined by Alembic revisions in `migrations/versions/`. The Flask app applies migrations on startup by default through `AUTO_MIGRATE=1`, so a missing `app.db` is created and upgraded automatically. Set `AUTO_MIGRATE=0` if you want to run migrations manually.

## User Scripts

Seed the starter users:

```bash
python scripts/seed_users.py
```

Starter users inserted by the seed script:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@example.com` | `admin123` |
| Player | `player@example.com` | `player123` |

Add a custom user:

```bash
python scripts/add_user.py --name "Admin User" --email admin@example.com --password admin123 --role admin
python scripts/add_user.py --name "Player User" --email player@example.com --password player123 --role player
```

Passwords are stored as Werkzeug password hashes, not plain text.

Inside Docker, run the same scripts through the container:

```bash
docker compose exec web python scripts/seed_users.py
docker compose exec web python scripts/add_user.py --name "New Player" --email new@example.com --password player123 --role player
```

## Run With Docker

Prerequisites:

- Docker Desktop or Docker Engine with Compose support.

Start the app:

```bash
docker compose up --build
```

Seed starter users in another terminal after the container is running:

```bash
docker compose exec web python scripts/seed_users.py
```

Open:

```text
http://localhost:5000
```

Stop the app:

```bash
docker compose down
```

The SQLite database is stored in the Docker volume `clicking_game_data`, mounted at `/app/instance`. This keeps `app.db` and user data when the container is recreated.

Reset the Docker database if you need a clean state:

```bash
docker compose down -v
docker compose up --build
docker compose exec web python scripts/seed_users.py
```

## Run Locally Without Docker

Prerequisites:

- Python 3.11 or newer.

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create starter users:

```bash
python scripts/seed_users.py
```

Run the development server:

```bash
$env:FLASK_DEBUG = "1"
python -m Clicking_Game.appp
```

Open:

```text
http://localhost:5000
```

## Alembic Migrations

Apply migrations manually:

```bash
python -m flask --app wsgi db-upgrade
```

Show the current migration revision:

```bash
python -m flask --app wsgi db-current
```

Create a new migration after changing SQLAlchemy models:

```bash
python -m alembic revision --autogenerate -m "describe change"
```

Review the generated migration before applying it. Then run:

```bash
python -m flask --app wsgi db-upgrade
```

Inside Docker:

```bash
docker compose exec web python -m flask --app wsgi db-upgrade
docker compose exec web python -m flask --app wsgi db-current
```

## Configuration

Environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | `dev-secret-change-me` | Flask session signing key. Change this before deployment. |
| `DATABASE` | `instance/app.db` | SQLite database file path used to build the SQLAlchemy URI. |
| `DATABASE_URL` | unset | Optional full SQLAlchemy database URI. Overrides `DATABASE` when set. |
| `AUTO_MIGRATE` | `1` | Set to `0` to stop the app from applying Alembic migrations on startup. |
| `HOST` | `0.0.0.0` | Local `app.py` bind host. |
| `PORT` | `5000` | Local `app.py` bind port. |
| `FLASK_DEBUG` | `0` | Set to `1` for local debug mode. |

Copy `.env.example` if you want a local reference for required variables. The app reads normal environment variables directly.

## Development Direction

The app is split into app factory, routes, models, utilities, migrations, and scripts so later changes can be added without putting everything in one file. Good next steps are:

1. Add tests for signup, login, role redirects, and score saving.
2. Add score submission routes that write through the `GameResult` SQLAlchemy model.
3. Replace starter credentials before any real deployment.
4. Add CSRF protection before accepting sensitive form submissions in production.
