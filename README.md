# Agile Web Project - Clicking Game

A Flask-based clicking game ("Egg Clicker") where players click an egg to
earn points, progress through egg tiers, and compete on a shared leaderboard.
The project includes:

- Role-based authentication (player and admin) with email verification.
- Persistent player progress (points, upgrades, current and highest egg
  tier) stored in SQLite through SQLAlchemy ORM models.
- A shared in-game leaderboard so players can see other users' scores
  alongside their own.
- Player history with an AI-powered performance feedback button backed by
  Google Gemini.
- An admin dashboard with searchable account management and aggregated game
  results.
- Alembic migrations, CSRF protection on every form, Werkzeug-hashed
  passwords, Docker support, a Render deployment configuration, and a CI
  workflow that runs `pytest` on every push.

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
|   |-- extensions.py            # Shared Flask extensions (Flask-Mail)
|   |-- game_logic.py            # EGG_CONFIG and clicking-game logic
|   |-- models/
|   |   |-- database.py          # SQLAlchemy engine/session and Alembic commands
|   |   `-- users.py             # User, GameResult, and GameState ORM models
|   |-- routes/
|   |   |-- auth.py              # Login, signup, email verification, dashboards, AI feedback
|   |   `-- main.py              # Home, guest, game page, leaderboard, and game API routes
|   |-- utils/
|   |   `-- auth.py              # login_required decorator and role checks
|   |-- static/                  # CSS, JavaScript, images
|   `-- templates/               # Jinja templates (base.html + page templates)
|-- migrations/
|   |-- env.py                   # Alembic migration environment
|   |-- script.py.mako           # Alembic revision template
|   `-- versions/                # Multiple Alembic revisions for schema changes
|-- scripts/
|   |-- add_user.py              # Add one local user to app.db
|   |-- create_admin.py          # Create a secure admin account for deployment
|   `-- seed_users.py            # Add local testing users to app.db
|-- tests/
|   |-- unit_tests.py            # Flask test-client unit and CSRF tests
|   |-- selenium_tests.py        # Selenium WebDriver browser tests
|   `-- test_system.py           # End-to-end system tests against a real SQLite DB
|-- .github/
|   `-- workflows/
|       `-- ci.yml               # GitHub Actions CI: runs pytest on every push/PR
|-- .env.example                 # Reference template for required environment variables
|-- alembic.ini
|-- docker-compose.yml
|-- Dockerfile
|-- pytest.ini
|-- render.yaml                  # Render deployment configuration
|-- requirements.txt
`-- wsgi.py                      # WSGI server entry point (used by waitress/Render)
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

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it. The command depends on your shell:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Git Bash, Linux, or macOS
source .venv/bin/activate
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

Run the development server. Set `FLASK_DEBUG=1` to enable debug mode:

```powershell
# Windows PowerShell
$env:FLASK_DEBUG = "1"
python -m Clicking_Game.app
```

```bash
# Git Bash, Linux, or macOS
FLASK_DEBUG=1 python -m Clicking_Game.app
```

Open:

```text
http://localhost:5000
```

## Testing

All tests live under `tests/` and use a separate test database (an in-memory
SQLite database for unit tests, a temporary SQLite file for system and
Selenium tests), so they never touch `instance/app.db`.

Run everything:

```bash
python -m pytest
```

Run a single suite or test:

```bash
python -m pytest tests/unit_tests.py
python -m pytest tests/selenium_tests.py::SeleniumTests::test_leaderboard_displays_player_rows_on_game_page
```

The suite covers password hashing, signup, login, role-based access control,
CSRF protection on every form, score saving, leaderboard ordering,
end-to-end signup/verification/login flows, and admin account management.
Selenium tests drive a headless Chrome browser through the home, login,
signup, dashboard, and game pages including the leaderboard and current-user
highlight.

Selenium tests **start their own Flask server automatically** on a free port
via `werkzeug.serving.make_server`, so you do not need to run the app
manually before running the tests. They require Chrome and a matching
`chromedriver` on `PATH`, and skip themselves automatically if either is
missing.

Every push and pull request against `main` runs the full pytest suite on
GitHub Actions (`.github/workflows/ci.yml`) using Python 3.11.

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

Optional integration variables (the app degrades gracefully if these are not
set — the AI-feedback button shows a "not configured" message and email
verification falls back to a development log):

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | unset | API key used by the player history page to generate AI performance feedback through Google Gemini. |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server used by Flask-Mail to send the signup verification email. |
| `MAIL_PORT` | `587` | SMTP port used by Flask-Mail. |
| `MAIL_USE_TLS` | `True` | Whether Flask-Mail should use STARTTLS. |
| `MAIL_USERNAME` | unset | SMTP account used to send verification emails. |
| `MAIL_PASSWORD` | unset | SMTP password or Gmail app password. Do not commit. |
| `MAIL_DEFAULT_SENDER` | `MAIL_USERNAME` | "From" address on outgoing verification emails. |

Optional admin setup variables used by `scripts/create_admin.py`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ADMIN_NAME` | unset | Optional admin display name for the admin creation script. |
| `ADMIN_EMAIL` | unset | Optional admin email for the admin creation script. |
| `ADMIN_PASSWORD` | unset | Optional admin password for the admin creation script. Do not commit real passwords. |

Copy `.env.example` if you want a local reference for required variables. The app reads normal environment variables directly.

## Deployment Notes

The repository ships a `render.yaml` describing a Render web service that
runs the app under `waitress-serve`. Render will pick this up automatically
when the repo is connected.

Before deploying the application:

1. Set a strong `SECRET_KEY` (the `render.yaml` uses `generateValue: true` so
   Render produces a random one on first deploy).
2. Do not use seeded local testing accounts.
3. Create a secure administrator account with `scripts/create_admin.py`.
4. Keep real credentials and production `.env` files out of version control.
5. Confirm automated tests pass with `python -m pytest`.
6. If using the AI feedback feature in production, set `GEMINI_API_KEY` as a
   Render secret.
7. If using real email verification in production, set `MAIL_USERNAME`,
   `MAIL_PASSWORD`, and `MAIL_DEFAULT_SENDER` as Render secrets.

## Development Direction

The app is split into app factory, routes, models, utilities, migrations,
scripts, and tests so later changes can be added without putting everything
in one file. Good next steps are:

1. Add more game-logic tests around upgrades, egg progression, and infinity
   levels.
2. Improve deployment documentation for production hosting.
3. Add monitoring and error logging for production use.
4. Review UI accessibility and responsive behaviour across devices.