# Agile Web Project - Clicking Game

A Flask clicking-game web app with role-based login, SQLAlchemy ORM models, Alembic migrations, SQLite persistence, and Docker support.

## Group Members

| UWA ID   | Name                   | GitHub Username    |
|----------|------------------------|--------------------|
| 24365316 | Audrey Chio            | audreycxy          |
| 24244417 | Sitong Liu             | Sitong888          |
| 24315125 | James Osmond           | James-909          |
| 24080064 | Handuo Cui             | cuihanduo1417595655|

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
|   |   `-- main.py              # Home, guest page, game page, and game API routes
|   |-- static/
|   `-- templates/
|-- migrations/
|   |-- env.py                   # Alembic migration environment
|   |-- script.py.mako           # Alembic revision template
|   `-- versions/
|       `-- 0001_create_initial_tables.py
|-- scripts/
|   |-- add_user.py              # Add one local user to app.db
|   |-- create_admin.py          # Create a secure admin account for deployment
|   `-- seed_users.py            # Add local testing users to app.db
|-- tests/
|   |-- unit_tests.py            # Unit tests for routes, authentication, CSRF, and score saving
|   `-- selenium_tests.py        # Selenium WebDriver system tests
|-- alembic.ini
|-- docker-compose.yml
|-- Dockerfile
|-- pytest.ini
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

## User and Account Setup

### Local development and testing

The project includes helper scripts for creating local development accounts.

Use the seed script only for local development or automated testing:

```bash
python scripts/seed_users.py
```

Seeded starter accounts are intended only for local testing. They should not be used for production or public deployment.

You can also create a custom local user:

```bash
python scripts/add_user.py --name "Local Player" --email local.player@example.com --password "replace-this-local-password" --role player
```

Do not document or commit real production credentials in README files, issues, screenshots, or `.env` files.

### Deployment account setup

Before deployment, create a real administrator account with a unique and secure password:

```bash
python scripts/create_admin.py
```

The admin creation script asks for the admin name, email, and password. It can also read values from environment variables.

For Git Bash or Linux/macOS terminal:

```bash
ADMIN_NAME="Site Admin" ADMIN_EMAIL="admin@example.com" ADMIN_PASSWORD="use-a-secure-password" python scripts/create_admin.py
```

For Windows PowerShell:

```powershell
$env:ADMIN_NAME="Site Admin"
$env:ADMIN_EMAIL="admin@example.com"
$env:ADMIN_PASSWORD="use-a-secure-password"
python scripts/create_admin.py
```

Inside Docker, run the same account setup script through the container:

```bash
docker compose exec web python scripts/create_admin.py
```

For production:

- Do not run `scripts/seed_users.py`.
- Do not use default local development credentials.
- Use a strong `SECRET_KEY`.
- Keep production credentials out of the repository.
- Create player accounts through the normal sign-up flow.
- Create administrator accounts through `scripts/create_admin.py`.

Passwords are stored as Werkzeug password hashes, not plain text.

## Run With Docker

Prerequisites:

- Docker Desktop or Docker Engine with Compose support.

Start the app:

```bash
docker compose up --build
```

For local development only, you may create test users in another terminal:

```bash
docker compose exec web python scripts/seed_users.py
```

For deployment, do not seed starter users. Create a secure administrator account instead:

```bash
docker compose exec web python scripts/create_admin.py
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
```

For local development, you may optionally seed test users again:

```bash
docker compose exec web python scripts/seed_users.py
```

For deployment, create a secure administrator account instead:

```bash
docker compose exec web python scripts/create_admin.py
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

For local development only, you may create test users:

```bash
python scripts/seed_users.py
```

For deployment or a production-like setup, create a secure administrator account instead:

```bash
python scripts/create_admin.py
```

Run the development server:

```bash
$env:FLASK_DEBUG = "1"
python -m Clicking_Game.app
```

Open:

```text
http://localhost:5000
```

## Automated Tests

Run the integration-style test suite:

```bash
python -m unittest discover -s tests -v
```

The tests boot the real Flask app against a temporary SQLite database and cover
public pages, signup/login/verification, role-based access control, profile
updates, account deletion, leaderboard responses, and game-state persistence.

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

Optional admin setup variables used by `scripts/create_admin.py`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ADMIN_NAME` | unset | Optional admin display name for the admin creation script. |
| `ADMIN_EMAIL` | unset | Optional admin email for the admin creation script. |
| `ADMIN_PASSWORD` | unset | Optional admin password for the admin creation script. Do not commit real passwords. |

Copy `.env.example` if you want a local reference for required variables. The app reads normal environment variables directly.

## Deployment Notes

Before deploying the application:

1. Set a strong `SECRET_KEY`.
2. Do not use seeded local testing accounts.
3. Create a secure administrator account with `scripts/create_admin.py`.
4. Keep real credentials and production `.env` files out of version control.
5. Confirm automated tests pass with `python -m pytest`.

## Development Direction

The app is split into app factory, routes, models, utilities, migrations, scripts, and tests so later changes can be added without putting everything in one file. Good next steps are:

1. Expand the automated tests to cover admin account updates, AI feedback success paths, and client-side browser interactions.
2. Add score submission routes that write through the `GameResult` SQLAlchemy model.
3. Replace starter credentials before any real deployment.
4. Add CSRF protection before accepting sensitive form submissions in production.
