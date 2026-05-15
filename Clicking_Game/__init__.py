# Setup File called by wsgi.py and Clicking_Game/app.py
import os
from pathlib import Path
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .models import database
from .routes import auth, main
from dotenv import load_dotenv
from .extensions import mail

csrf = CSRFProtect()

# Helper function to construct a SQLite URI from a file path
def _sqlite_uri(database_path):
    if database_path == ":memory:":
        return "sqlite:///:memory:"
    return f"sqlite:///{Path(database_path).resolve().as_posix()}"

# Helper function to parse boolean environment variables
def _bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Building and configuring the Flask application
def create_app(test_config=None):
    load_dotenv()
    
    project_root = Path(__file__).resolve().parent.parent
    instance_path = project_root / "instance"
    default_database = instance_path / "app.db"

    # Create the Flask appication
    app = Flask(
        __name__,
        instance_path=str(instance_path),
        instance_relative_config=True,
    )
    # Sets configuration values
    app.config.from_mapping(
        PROJECT_ROOT=project_root,
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE=os.environ.get("DATABASE", str(default_database)),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL"),
        AUTO_MIGRATE=_bool_env("AUTO_MIGRATE", True),

        # Avatar upload settings. Files land under instance/uploads/avatars/
        # so they sit alongside app.db and do not need to be in the source
        # tree. MAX_CONTENT_LENGTH protects the server from huge uploads.
        UPLOAD_FOLDER=str(instance_path / "uploads" / "avatars"),
        MAX_CONTENT_LENGTH=1 * 1024 * 1024,  # 1 MB
        ALLOWED_AVATAR_EXTENSIONS={"png", "jpg", "jpeg", "gif"},

        MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_PORT=int(os.environ.get("MAIL_PORT", 587)),
        MAIL_USE_TLS=_bool_env("MAIL_USE_TLS", True),
        MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
        MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.environ.get(
            "MAIL_DEFAULT_SENDER",
            os.environ.get("MAIL_USERNAME")
        ),

        # When set, signup uses the Resend HTTPS API to send the verification
        # email. This is required on hosts like Render free that block
        # outbound SMTP (ports 25 / 465 / 587). When unset, the app falls
        # back to Flask-Mail SMTP, which is the simpler path locally.
        RESEND_API_KEY=os.environ.get("RESEND_API_KEY"),
    )
    app.config.from_prefixed_env()

    if test_config is not None:
        app.config.update(test_config)

    # Ensure the instance folder exists and create parent directories for the database if needed
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    if app.config["DATABASE"] != ":memory:":
        Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = _sqlite_uri(app.config["DATABASE"])

    # Initializes database connection, CSRF protection, mail service, and registers route files
    database.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)

    # Automatically apply database migrations if enabled
    if app.config["AUTO_MIGRATE"]:
        with app.app_context():
            database.upgrade_db()

    return app

