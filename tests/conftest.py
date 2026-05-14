import pytest

from Clicking_Game import create_app
from Clicking_Game.models import database, users


@pytest.fixture()
def app(tmp_path):
    test_db = tmp_path / "test_app.sqlite"

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "DATABASE": str(test_db),
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{test_db}",
            "AUTO_MIGRATE": False,
        }
    )

    with app.app_context():
        database.Base.metadata.create_all(bind=app.extensions["sqlalchemy_engine"])

    yield app

    with app.app_context():
        database.SessionLocal.remove()
        database.Base.metadata.drop_all(bind=app.extensions["sqlalchemy_engine"])


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def create_verified_user(
    name="Test Player",
    email="player@example.com",
    password="Password123",
    role="player",
):
    user = users.create_user(
        name=name,
        email=email,
        password=password,
        role=role,
    )

    user.email_verified = True

    db_session = database.get_session()
    db_session.commit()

    return user