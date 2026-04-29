# Setting up the database connection and Alembic integration for migrations.
import click
from alembic import command
from alembic.config import Config
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass

SessionLocal = scoped_session(sessionmaker(autoflush=False, expire_on_commit=False))
_engine = None

# Gives a database session
def get_session():
    return SessionLocal()

def get_alembic_config(app):
    project_root = app.config["PROJECT_ROOT"]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "migrations"))
    config.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])
    return config

# Runs Alembic migrations
def upgrade_db(revision="head"):
    """Apply Alembic migrations up to the requested revision."""
    command.upgrade(get_alembic_config(current_app), revision)

# Shows the current migration revision
def current_revision():
    command.current(get_alembic_config(current_app), verbose=True)

# Cleans up database session after request
def close_session(_error=None):
    SessionLocal.remove()

@click.command("db-upgrade")
@click.argument("revision", default="head")
@with_appcontext
def upgrade_db_command(revision):
    upgrade_db(revision)
    click.echo(f"Database upgraded to {revision}.")

@click.command("init-db")
@with_appcontext
def init_db_command():
    upgrade_db("head")
    click.echo("Database initialized with Alembic migrations.")

@click.command("db-current")
@with_appcontext
def current_db_command():
    current_revision()

# Connects SQLAlchemy to the Flask app
def init_app(app):
    global _engine

    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"], future=True)
    _engine = engine
    app.extensions["sqlalchemy_engine"] = engine
    SessionLocal.remove()
    SessionLocal.configure(bind=engine)

    app.teardown_appcontext(close_session)
    app.cli.add_command(upgrade_db_command)
    app.cli.add_command(init_db_command)
    app.cli.add_command(current_db_command)
