# Unit tests for core backend behaviours.
# This file focuses on authentication redirects, role-based access control,
# score saving, CSRF protection, and password hashing.

import html
import re
import unittest

from Clicking_Game import create_app
from Clicking_Game.models import database, users


class BasicTests(unittest.TestCase):
    # Basic unit tests with CSRF disabled.
    # These tests use Flask's test client and an in-memory SQLite database,
    # so they run quickly and do not affect the real application database.

    def setUp(self):
        # Create a temporary app and in-memory database before each test.
        self.testApp = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "WTF_CSRF_ENABLED": False,
                "DATABASE": ":memory:",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "AUTO_MIGRATE": False,
            }
        )

        self.client = self.testApp.test_client()
        self.app_context = self.testApp.app_context()
        self.app_context.push()

        database.Base.metadata.create_all(
            bind=self.testApp.extensions["sqlalchemy_engine"]
        )

    def tearDown(self):
        # Clean up database tables, sessions, and app context after each test.
        engine = self.testApp.extensions["sqlalchemy_engine"]

        database.SessionLocal.remove()
        database.Base.metadata.drop_all(bind=engine)
        database.SessionLocal.remove()
        engine.dispose()

        self.app_context.pop()

        self.client = None
        self.testApp = None

    def create_verified_user(
        self,
        name="Test Player",
        email="player@example.com",
        password="Password123",
        role="player",
    ):
        # Helper for creating a verified user for login and access-control tests.
        user = users.create_user(
            name=name,
            email=email,
            password=password,
            role=role,
        )

        user.email_verified = True
        database.get_session().commit()

        return user

    def login(self, email="player@example.com", password="Password123"):
        # Helper for posting login credentials to the login route.
        return self.client.post(
            "/login",
            data={
                "email": email,
                "password": password,
            },
            follow_redirects=False,
        )

    def test_password_hashing(self):
        # Check that passwords are stored as hashes and not as plain text.
        plain_password = "Password123"

        user = users.create_user(
            name="Hash Test User",
            email="hash@example.com",
            password=plain_password,
            role="player",
        )

        self.assertIsNotNone(user)
        self.assertNotEqual(user.password_hash, plain_password)
        self.assertTrue(user.check_password(plain_password))
        self.assertFalse(user.check_password("WrongPassword"))

    def test_signup_with_valid_user_details(self):
        # Check that a valid signup creates a player account.
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

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Account created", response.data)

        created_user = users.get_by_email("newplayer@example.com")

        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.name, "New Player")
        self.assertEqual(created_user.role, "player")

    def test_login_with_valid_account_details_redirects_player(self):
        # Check that a verified player can log in and is redirected to the player dashboard.
        self.create_verified_user(
            name="Player User",
            email="player@example.com",
            password="Password123",
            role="player",
        )

        response = self.login(
            email="player@example.com",
            password="Password123",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/player_dashboard", response.headers["Location"])

    def test_login_with_invalid_account_details(self):
        # Check that incorrect login details return the expected error message.
        response = self.login(
            email="wrong@example.com",
            password="WrongPassword",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password", response.data)

    def test_player_role_redirects_to_player_dashboard(self):
        # Check that players are redirected to the player dashboard after login.
        self.create_verified_user(
            name="Player User",
            email="player@example.com",
            password="Password123",
            role="player",
        )

        response = self.login(
            email="player@example.com",
            password="Password123",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/player_dashboard", response.headers["Location"])

    def test_admin_role_redirects_to_admin_dashboard(self):
        # Check that admins are redirected to the admin dashboard after login.
        self.create_verified_user(
            name="Admin User",
            email="admin@example.com",
            password="Password123",
            role="admin",
        )

        response = self.login(
            email="admin@example.com",
            password="Password123",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin_dashboard", response.headers["Location"])

    def test_player_cannot_access_admin_dashboard(self):
        # Check that a player cannot access the admin dashboard.
        self.create_verified_user(
            name="Player User",
            email="player@example.com",
            password="Password123",
            role="player",
        )

        self.login(
            email="player@example.com",
            password="Password123",
        )

        response = self.client.get(
            "/admin_dashboard",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_admin_cannot_access_player_dashboard(self):
        # Check that an admin cannot access the player dashboard route.
        self.create_verified_user(
            name="Admin User",
            email="admin@example.com",
            password="Password123",
            role="admin",
        )

        self.login(
            email="admin@example.com",
            password="Password123",
        )

        response = self.client.get(
            "/player_dashboard",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_logged_in_player_can_save_score(self):
        # Check that a logged-in player can sync game progress and create a saved result.
        player = self.create_verified_user(
            name="Score Player",
            email="scoreplayer@example.com",
            password="Password123",
            role="player",
        )

        self.login(
            email="scoreplayer@example.com",
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

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(data["new_points"], 1)

        saved_results = users.list_results(user_id=player.id)

        self.assertEqual(len(saved_results), 1)
        self.assertEqual(saved_results[0].score, data["new_points"])

    def test_guest_user_cannot_save_score(self):
        # Check that anonymous guest users cannot save scores through the sync API.
        response = self.client.post(
            "/api/sync",
            json={},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        saved_results = users.list_results()

        self.assertEqual(saved_results, [])

    def test_player_dashboard_displays_highest_egg(self):
        # Check that the player dashboard loads and displays the highest egg section.
        self.create_verified_user(
            name="Dashboard Player",
            email="dashboard@example.com",
            password="Password123",
            role="player",
        )

        self.login(
            email="dashboard@example.com",
            password="Password123",
        )

        response = self.client.get("/player_dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Highest Egg", response.data)
        self.assertIn(b"Standard", response.data)

    def test_game_page_leaderboard_ranks_players_by_points(self):
        """Top players appear on the /game leaderboard in descending point order."""
        db_session = database.get_session()

        for name, email, points in [
            ("Alice", "alice@example.com", 500),
            ("Bob", "bob@example.com", 1000),
            ("Carol", "carol@example.com", 250),
        ]:
            player = self.create_verified_user(
                name=name,
                email=email,
                password="Password123",
                role="player",
            )
            db_session.add(
                users.GameState(
                    user_id=player.id,
                    points=points,
                    current_infinity_level=0,
                    current_type="standard",
                    highest_type="standard",
                    clicks_remaining=10,
                    click_power_lvl=1,
                    autoclicker_lvl=0,
                )
            )

        db_session.commit()

        # /game is public, so a guest request still gets the leaderboard
        response = self.client.get("/game")
        self.assertEqual(response.status_code, 200)

        body = response.data.decode("utf-8")

        # Pull out just the leaderboard <ul> so we don't accidentally match
        # player names that appear elsewhere on the page
        leaderboard_match = re.search(
            r'<ul class="list-group list-group-flush">(.*?)</ul>',
            body,
            re.DOTALL,
        )

        self.assertIsNotNone(leaderboard_match, "Leaderboard <ul> not found in /game response")

        leaderboard_html = leaderboard_match.group(1)

        # Extract names in the order they appear: "1. Bob", "2. Alice", ...
        names_in_order = re.findall(r"\d+\.\s*([A-Za-z]+)", leaderboard_html)

        self.assertEqual(
            names_in_order[:3],
            ["Bob", "Alice", "Carol"],
            "Leaderboard should be sorted by GameState.points descending",
        )


class CSRFTests(unittest.TestCase):
    # Unit tests for CSRF protection.
    # These tests turn CSRF protection on and check that sensitive routes
    # reject missing tokens. They also check that pages provide tokens where needed.

    def setUp(self):
        # Create a temporary app with CSRF protection enabled.
        self.testApp = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret-key",
                "WTF_CSRF_ENABLED": True,
                "DATABASE": ":memory:",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "AUTO_MIGRATE": False,
            }
        )

        self.client = self.testApp.test_client()
        self.app_context = self.testApp.app_context()
        self.app_context.push()

        database.Base.metadata.create_all(
            bind=self.testApp.extensions["sqlalchemy_engine"]
        )

    def tearDown(self):
        # Clean up database tables, sessions, and app context after each CSRF test.
        engine = self.testApp.extensions["sqlalchemy_engine"]

        database.SessionLocal.remove()
        database.Base.metadata.drop_all(bind=engine)
        database.SessionLocal.remove()
        engine.dispose()

        self.app_context.pop()

        self.client = None
        self.testApp = None

    def get_csrf_token(self, url):
        # Extract a CSRF token from either a hidden form input or a meta tag.
        response = self.client.get(url)
        page = response.data.decode("utf-8")

        input_match = re.search(
            r'name="csrf_token"[^>]*value="([^"]+)"',
            page,
        )

        if input_match:
            return html.unescape(input_match.group(1))

        meta_match = re.search(
            r'name="csrf-token"[^>]*content="([^"]+)"',
            page,
        )

        if meta_match:
            return html.unescape(meta_match.group(1))

        return None

    def create_verified_user(
        self,
        name="Test Player",
        email="player@example.com",
        password="Password123",
        role="player",
    ):
        # Helper for creating a verified user for CSRF-protected tests.
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
        # Log in using a valid CSRF token.
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
        # Check that login rejects POST requests without a CSRF token.
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
        # Check that signup rejects POST requests without a CSRF token.
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
        # Check that signup works when a valid CSRF token is submitted.
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
        # Check that profile updates are rejected without a CSRF token.
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
        # Check that score sync requests are rejected without a CSRF token.
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
        # Check that the game page includes a CSRF meta token for JavaScript requests.
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