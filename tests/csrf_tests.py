import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from Clicking_Game import create_app
from Clicking_Game.models import database, users


class CSRFTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        test_db = Path(self.temp_dir.name) / "csrf_test_app.sqlite"

        self.testApp = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "DATABASE": str(test_db),
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{test_db}",
                "AUTO_MIGRATE": False,
                "WTF_CSRF_ENABLED": True,
            }
        )

        self.client = self.testApp.test_client()
        self.app_context = self.testApp.app_context()
        self.app_context.push()

        database.Base.metadata.create_all(
            bind=self.testApp.extensions["sqlalchemy_engine"]
        )

    def tearDown(self):
        engine = self.testApp.extensions["sqlalchemy_engine"]

        database.SessionLocal.remove()
        database.Base.metadata.drop_all(bind=engine)
        database.SessionLocal.remove()
        engine.dispose()

        self.app_context.pop()

        self.client = None
        self.testApp = None

        self.temp_dir.cleanup()

    def get_csrf_token(self, url):
        response = self.client.get(url)
        soup = BeautifulSoup(response.data, "html.parser")
        token_input = soup.find("input", {"name": "csrf_token"})

        if token_input:
            return token_input.get("value")

        meta_token = soup.find("meta", {"name": "csrf-token"})

        if meta_token:
            return meta_token.get("content")

        return None

    def create_verified_user(
        self,
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
        database.get_session().commit()

        return user

    def login_with_csrf(self, email="player@example.com", password="Password123"):
        csrf_token = self.get_csrf_token("/login")

        return self.client.post(
            "/login",
            data={
                "email": email,
                "password": password,
                "csrf_token": csrf_token,
            },
            follow_redirects=False,
        )

    def test_login_rejects_missing_csrf_token(self):
        response = self.client.post(
            "/login",
            data={
                "email": "player@example.com",
                "password": "Password123",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 400)

    def test_signup_rejects_missing_csrf_token(self):
        response = self.client.post(
            "/signup",
            data={
                "username": "New Player",
                "email": "newplayer@example.com",
                "password": "Password123",
                "confirm_password": "Password123",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 400)

    def test_signup_accepts_valid_csrf_token(self):
        csrf_token = self.get_csrf_token("/signup")

        response = self.client.post(
            "/signup",
            data={
                "username": "New Player",
                "email": "newplayer@example.com",
                "password": "Password123",
                "confirm_password": "Password123",
                "csrf_token": csrf_token,
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account created", response.data)

    def test_profile_update_rejects_missing_csrf_token(self):
        self.create_verified_user(
            name="Profile Player",
            email="profile@example.com",
            password="Password123",
            role="player",
        )

        self.login_with_csrf(
            email="profile@example.com",
            password="Password123",
        )

        response = self.client.post(
            "/profile",
            data={
                "username": "Updated Player",
                "email": "updated@example.com",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 400)

    def test_score_submission_rejects_missing_csrf_token(self):
        player = self.create_verified_user(
            name="Score Player",
            email="score@example.com",
            password="Password123",
            role="player",
        )

        self.login_with_csrf(
            email="score@example.com",
            password="Password123",
        )

        db_session = database.get_session()

        game_state = users.GameState(
            user_id=player.id,
            points=0,
            current_infinity_level=0,
            current_type="standard",
            highest_type="standard",
            clicks_remaining=10,
            click_power_lvl=1,
            autoclicker_lvl=0,
        )

        db_session.add(game_state)
        db_session.commit()

        response = self.client.post(
            "/api/sync",
            json={},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 400)

    def test_game_page_includes_csrf_token_for_score_submission(self):
        self.create_verified_user(
            name="Game Player",
            email="gamecsrf@example.com",
            password="Password123",
            role="player",
        )

        self.login_with_csrf(
            email="gamecsrf@example.com",
            password="Password123",
        )

        response = self.client.get("/game")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="csrf-token"', response.data)


if __name__ == "__main__":
    unittest.main()