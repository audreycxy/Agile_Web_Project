# Agile Web Project - Clicking Game

A Flask clicking-game web app with role-based login, SQLAlchemy ORM models, Alembic migrations, SQLite persistence, email verification, account management, automated testing, and Docker/Render deployment support.

## Current Structure

```text
.
|-- .github/
|   `-- workflows/
|       `-- ci.yml                # GitHub Actions workflow for automated tests
|-- Clicking_Game/
|   |-- __init__.py              # Flask app factory, configuration, CSRF, mail, and blueprints
|   |-- app.py                   # Local development entry point
|   |-- extensions.py            # Shared Flask extensions, including Flask-Mail
|   |-- game_logic.py            # Egg configuration and game logic data
|   |-- models/
|   |   |-- database.py          # SQLAlchemy engine/session and Alembic commands
|   |   `-- users.py             # User, game state, and game-result ORM models
|   |-- routes/
|   |   |-- auth.py              # Login, signup, email verification, logout, dashboards, profile
|   |   `-- main.py              # Home, guest page, game page, leaderboard, and game API routes
|   |-- static/
|   |   |-- css/
|   |   |   `-- style.css        # Shared theme, auth, dashboard, admin, profile, and game page styles
|   |   `-- js/
|   |       |-- admin_player_results.js
|   |       |-- game.js           # Main game interaction logic
|   |       |-- history.js
|   |       |-- home.js           # Home page mini preview and section navigation
|   |       |-- login.js          # Login validation and password visibility toggle
|   |       |-- player_dashboard.js
|   |       |-- profile.js        # Profile password visibility toggle
|   |       `-- signup.js         # Signup validation and password visibility toggle
|   `-- templates/
|       |-- base.html            # Shared base template for Bootstrap, styles, and page blocks
|       |-- admin/               # Admin dashboard, account management, and results pages
|       |-- player/              # Player dashboard, profile, history, and game pages
|       `-- public/              # Home, guest, login, and signup pages
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
|   |-- unit_tests.py            # Unit tests for authentication, CSRF, score saving, and password hashing
|   |-- selenium_tests.py        # Selenium WebDriver browser-based system tests
|   `-- test_system.py           # Flask client system tests for full route workflows
|-- .env.example                 # Example environment variable configuration
|-- alembic.ini
|-- docker-compose.yml
|-- Dockerfile
|-- pytest.ini
|-- render.yaml                  # Render deployment configuration
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

The schema is defined by Alembic revisions in `migrations/versions/`. The Flask app applies migrations on startup by default through `AUTO_MIGRATE=1`, so a missing `app.db` is created and upgraded automatically.

Set `AUTO_MIGRATE=0` if you want to run migrations manually.

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

### Email verification

Newly registered users must verify their email address before logging in.

In local development, email sending can be suppressed or configured through environment variables. In production, SMTP settings must be configured before accepting real user signups.

During development, the signup page may display a verification link to help test the email verification flow.

### Account management

Players can manage their own account from the profile page. They can:

- update their username
- update their email
- change their password
- delete their account after confirming their current password

Administrators can use the admin accounts page to:

- search registered accounts
- filter accounts by role
- review account status
- change user roles
- activate or deactivate accounts

Account management forms are protected with CSRF tokens.

### Deployment account setup

Before deployment, create a real administrator account with a unique and secure password:

```bash
python scripts/create_admin.py
```

The admin creation script asks for the admin name, email, and password. It can also read values from environment variables.

For Git Bash or Linux/macOS terminal:

```bash
ADMIN_NAME="Site Admin" ADMIN_EMAIL="admin@your-domain.example" ADMIN_PASSWORD="use-a-secure-password" python scripts/create_admin.py
```

For Windows PowerShell:

```powershell
$env:ADMIN_NAME="Site Admin"
$env:ADMIN_EMAIL="admin@your-domain.example"
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
- Configure email verification settings.
- Create player accounts through the normal sign-up flow.
- Create administrator accounts through `scripts/create_admin.py`.

Passwords are stored as Werkzeug password hashes, not plain text.

## Frontend Features

The project uses a shared visual theme across public, authentication, dashboard, admin, profile, and game pages.

Main frontend behaviours include:

- home page mini egg preview
- active section highlighting for home page navigation
- login and signup form validation
- password show/hide toggles on login, signup, and profile pages
- player dashboard game navigation
- game interaction and progress syncing
- profile account update and account deletion forms
- admin account search, role filtering, and account status controls

Most pages extend `templates/base.html`, which centralises shared page structure, Bootstrap, Google Fonts, the project stylesheet, and page-specific blocks.

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

## Testing

Run all automated tests:

```bash
python -m pytest
```

The project includes unit tests, Flask client system tests, and Selenium WebDriver tests.

### Unit tests

The unit tests focus on smaller backend behaviours such as:

- signup
- login with valid and invalid details
- player/admin role redirects
- access control between admin and player pages
- score saving through `/api/sync`
- guest users being blocked from score saving
- CSRF protection for sensitive submissions
- password hashing

### Flask client system tests

The Flask client system tests cover wider route workflows without opening a real browser, including:

- public page loading
- guest game initial state
- signup and email verification flow
- unverified user login blocking
- protected route redirects
- player and admin login redirects
- profile update
- account deletion
- game state saving and restart
- leaderboard filtering and ranking
- history page score statistics
- AI feedback fallback when the Gemini API key is not configured

These tests use Flask's test client and a temporary SQLite test database.

### Selenium WebDriver tests

The Selenium tests cover browser-based user flows such as:

- loading the home page
- opening the login page
- opening the signup page
- completing the signup flow
- logging in as a player
- opening the player dashboard
- using the Start Game button

The tests use isolated test databases instead of the real local `instance/app.db`.

- Unit tests use an in-memory SQLite test database.
- Flask client system tests use a temporary SQLite test database file.
- Selenium tests use a temporary SQLite test database file.
- Selenium tests start the Flask test server automatically, so you do not need to manually run the app before running the test suite.

## Continuous Integration

The project includes a GitHub Actions workflow in:

```text
.github/workflows/ci.yml
```

The workflow runs automatically on pushes and pull requests to `main`.

It installs dependencies from `requirements.txt` and runs the automated tests with:

```bash
pytest tests/ -v
```

The CI workflow uses test environment variables and a separate test database, so it does not depend on the local development database.

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
| `GEMINI_API_KEY` | unset | Optional API key used for AI feedback features. |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server used for email verification. |
| `MAIL_PORT` | `587` | SMTP server port. |
| `MAIL_USE_TLS` | `1` | Enables TLS for email sending. |
| `MAIL_USERNAME` | unset | SMTP account username. |
| `MAIL_PASSWORD` | unset | SMTP account password or app password. Do not commit real values. |
| `MAIL_DEFAULT_SENDER` | `MAIL_USERNAME` | Default sender address for verification emails. |
| `MAIL_SUPPRESS_SEND` | unset | Set to `true` in tests or local environments if emails should not be sent. |

Optional admin setup variables used by `scripts/create_admin.py`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ADMIN_NAME` | unset | Optional admin display name for the admin creation script. |
| `ADMIN_EMAIL` | unset | Optional admin email for the admin creation script. |
| `ADMIN_PASSWORD` | unset | Optional admin password for the admin creation script. Do not commit real passwords. |

Copy `.env.example` if you want a local reference for required variables. The app reads normal environment variables directly.

## Render Deployment

The project includes a `render.yaml` file for deployment on Render.

The Render configuration installs dependencies from `requirements.txt` and starts the app with Waitress:

```bash
waitress-serve --listen=0.0.0.0:$PORT wsgi:app
```

Before deploying, configure production environment variables in Render, especially:

- `SECRET_KEY`
- `DATABASE` or `DATABASE_URL`
- `AUTO_MIGRATE`
- `GEMINI_API_KEY` if AI feedback is used
- `MAIL_SERVER`
- `MAIL_PORT`
- `MAIL_USE_TLS`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`

Do not commit real production secrets to the repository.

## Deployment Notes

Before deploying the application:

1. Set a strong `SECRET_KEY`.
2. Do not use seeded local testing accounts.
3. Create a secure administrator account with `scripts/create_admin.py`.
4. Configure email verification settings before accepting real signups.
5. Keep real credentials and production `.env` files out of version control.
6. Confirm automated tests pass with `python -m pytest`.

## Development Direction

The app is split into app factory, routes, models, utilities, migrations, scripts, templates, static assets, tests, and deployment configuration so later changes can be added without putting everything in one file.

Good next steps are:

1. Continue expanding automated tests for edge cases in game logic, profile updates, and admin workflows.
2. Improve production deployment documentation and monitoring.
3. Add error logging for production use.
4. Review UI accessibility and responsive behaviour across devices.