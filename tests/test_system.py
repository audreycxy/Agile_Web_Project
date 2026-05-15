import os
import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from Clicking_Game import create_app
from Clicking_Game.models import database, users


class SystemTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test_app.db"
        self.app = create_app(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "AUTO_MIGRATE": False,
                "DATABASE": str(self.database_path),
                "SECRET_KEY": "test-secret",
            }
        )

        with self.app.app_context():
            database.Base.metadata.create_all(
                bind=self.app.extensions["sqlalchemy_engine"]
            )

        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            database.SessionLocal.remove()
            self.app.extensions["sqlalchemy_engine"].dispose()

        self.temp_dir.cleanup()

    def create_user(
        self,
        *,
        name="Player One",
        email="player@example.com",
        password="password123",
        role="player",
        email_verified=True,
        is_active=True,
        is_deleted=False,
        points=0,
        current_infinity_level=0,
        current_type="standard",
        highest_type="standard",
        clicks_remaining=None,
        progress_percent=0,
    ):
        with self.app.app_context():
            user = users.create_user(name, email, password, role=role)
            self.assertIsNotNone(user)

            stored_user = users.get_by_id(user.id)
            stored_user.email_verified = email_verified
            stored_user.email_verification_token = None if email_verified else stored_user.email_verification_token
            stored_user.is_active = is_active
            stored_user.is_deleted = is_deleted
            stored_user.deleted_at = datetime.utcnow() if is_deleted else None
            stored_user.points = points
            stored_user.current_infinity_level = current_infinity_level
            stored_user.current_type = current_type
            stored_user.highest_type = highest_type
            stored_user.clicks_remaining = clicks_remaining
            stored_user.progress_percent = progress_percent
            database.get_session().commit()

            return stored_user.id

    def create_result(self, user_id, score, duration_seconds=None):
        with self.app.app_context():
            return users.create_game_result(user_id, score, duration_seconds)

    def login_session(self, user_id):
        with self.app.app_context():
            user = users.get_by_id(user_id)

        with self.client.session_transaction() as session:
            session["user_id"] = user.id
            session["email"] = user.email
            session["name"] = user.name
            session["role"] = user.role

    def get_user(self, user_id):
        with self.app.app_context():
            return users.get_by_id(user_id)

    def test_public_pages_load(self):
        for path in ("/", "/login", "/signup", "/guest", "/game"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_guest_game_page_uses_guest_initial_state(self):
        response = self.client.get("/game")
        page = response.get_data(as_text=True)

        self.assertIn('"is_guest": true', page)
        self.assertIn('"points": 0', page)
        self.assertIn("Loading leaderboard...", page)

    def test_signup_creates_unverified_user_and_shows_verification_link(self):
        response = self.client.post(
            "/signup",
            data={
                "username": "New Player",
                "email": "newplayer@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
        )
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Account created. Please verify your email before logging in.", page)
        self.assertIn("Development verification link:", page)

        with self.app.app_context():
            user = users.get_by_email("newplayer@example.com")
            self.assertIsNotNone(user)
            self.assertFalse(user.email_verified)
            self.assertIsNotNone(user.email_verification_token)

    def test_unverified_user_must_verify_before_login(self):
        user_id = self.create_user(
            email="needsverify@example.com",
            email_verified=False,
        )
        user = self.get_user(user_id)

        blocked_login = self.client.post(
            "/login",
            data={"email": user.email, "password": "password123"},
        )
        self.assertIn(
            "Please verify your email before logging in.",
            blocked_login.get_data(as_text=True),
        )

        verify_response = self.client.get(f"/verify-email/{user.email_verification_token}")
        self.assertIn(
            "Email verified successfully. You can now log in.",
            verify_response.get_data(as_text=True),
        )

        successful_login = self.client.post(
            "/login",
            data={"email": user.email, "password": "password123"},
            follow_redirects=False,
        )
        self.assertEqual(successful_login.status_code, 302)
        self.assertTrue(successful_login.headers["Location"].endswith("/player_dashboard"))

    def test_protected_routes_redirect_anonymous_users_to_login(self):
        protected_get_routes = (
            "/player_dashboard",
            "/history",
            "/profile",
            "/admin_dashboard",
            "/admin_accounts",
            "/admin_player_results",
        )

        for path in protected_get_routes:
            response = self.client.get(path, follow_redirects=False)
            self.assertEqual(response.status_code, 302, path)
            self.assertTrue(response.headers["Location"].endswith("/login"))

        post_response = self.client.post(
            "/save_game_state",
            json={"points": 25},
            follow_redirects=False,
        )
        self.assertEqual(post_response.status_code, 302)
        self.assertTrue(post_response.headers["Location"].endswith("/login"))

    def test_player_login_redirects_to_dashboard(self):
        self.create_user(email="playerlogin@example.com")

        response = self.client.post(
            "/login",
            data={"email": "playerlogin@example.com", "password": "password123"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/player_dashboard"))

    def test_admin_login_redirects_to_admin_dashboard(self):
        self.create_user(
            name="Admin User",
            email="admin@example.com",
            role="admin",
        )

        response = self.client.post(
            "/login",
            data={"email": "admin@example.com", "password": "password123"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin_dashboard"))

    def test_player_cannot_access_admin_routes_but_admin_can(self):
        player_id = self.create_user(email="regular@example.com")
        self.login_session(player_id)

        blocked_response = self.client.get("/admin_dashboard", follow_redirects=False)
        self.assertEqual(blocked_response.status_code, 302)
        self.assertTrue(blocked_response.headers["Location"].endswith("/login"))

        admin_id = self.create_user(
            name="Admin Two",
            email="admintwo@example.com",
            role="admin",
        )
        self.login_session(admin_id)

        allowed_response = self.client.get("/admin_dashboard")
        self.assertEqual(allowed_response.status_code, 200)
        self.assertIn("Current platform summary", allowed_response.get_data(as_text=True))

    def test_profile_update_changes_name_email_and_password(self):
        user_id = self.create_user(email="profile@example.com")
        self.login_session(user_id)

        response = self.client.post(
            "/profile",
            data={
                "username": "Updated Player",
                "email": "updated@example.com",
                "current_password": "password123",
                "new_password": "newpassword456",
                "confirm_password": "newpassword456",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Profile updated.", response.get_data(as_text=True))

        updated_user = self.get_user(user_id)
        self.assertEqual(updated_user.name, "Updated Player")
        self.assertEqual(updated_user.email, "updated@example.com")
        self.assertTrue(updated_user.check_password("newpassword456"))

    def test_delete_account_soft_deletes_user_and_blocks_future_login(self):
        user_id = self.create_user(email="delete-me@example.com")
        self.login_session(user_id)

        response = self.client.post("/profile/delete", data={"delete_password": "password123"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("account_deleted=1", response.headers["Location"])

        deleted_user = self.get_user(user_id)
        self.assertTrue(deleted_user.is_deleted)
        self.assertFalse(deleted_user.is_active)

        login_response = self.client.post(
            "/login",
            data={"email": "delete-me@example.com", "password": "password123"},
        )
        self.assertIn("This account has been deleted.", login_response.get_data(as_text=True))

    def test_save_game_state_and_restart_game_update_persistent_progress(self):
        user_id = self.create_user(email="gamer@example.com")
        self.login_session(user_id)

        save_response = self.client.post(
            "/save_game_state",
            json={
                "points": 275,
                "current_infinity_level": 4,
                "current_type": "water",
                "highest_type": "gold",
                "clicks_remaining": 7,
                "progress_percent": 63,
            },
        )
        self.assertEqual(save_response.status_code, 200)
        self.assertEqual(save_response.get_json(), {"success": True})

        saved_user = self.get_user(user_id)
        self.assertEqual(saved_user.points, 275)
        self.assertEqual(saved_user.current_infinity_level, 4)
        self.assertEqual(saved_user.current_type, "water")
        self.assertEqual(saved_user.highest_type, "gold")
        self.assertEqual(saved_user.clicks_remaining, 7)
        self.assertEqual(saved_user.progress_percent, 63)

        game_page = self.client.get("/game").get_data(as_text=True)
        self.assertIn('"is_guest": false', game_page)
        self.assertIn('"points": 275', game_page)
        self.assertIn('"current_type": "water"', game_page)

        restart_response = self.client.post("/restart_game")
        self.assertEqual(restart_response.status_code, 200)
        self.assertEqual(restart_response.get_json(), {"success": True})

        reset_user = self.get_user(user_id)
        self.assertEqual(reset_user.points, 0)
        self.assertEqual(reset_user.current_infinity_level, 0)
        self.assertEqual(reset_user.current_type, "standard")
        self.assertEqual(reset_user.highest_type, "standard")
        self.assertIsNone(reset_user.clicks_remaining)
        self.assertEqual(reset_user.progress_percent, 0)

    def test_leaderboard_returns_only_active_non_deleted_players_in_rank_order(self):
        self.create_user(
            name="Low Score",
            email="low@example.com",
            points=10,
            current_infinity_level=1,
        )
        high_id = self.create_user(
            name="High Score",
            email="high@example.com",
            points=90,
            current_infinity_level=1,
        )
        tie_break_id = self.create_user(
            name="Tie Break",
            email="tie@example.com",
            points=90,
            current_infinity_level=3,
        )
        self.create_user(
            name="Inactive Player",
            email="inactive@example.com",
            points=999,
            is_active=False,
        )
        self.create_user(
            name="Deleted Player",
            email="deleted@example.com",
            points=1000,
            is_deleted=True,
        )
        self.create_user(
            name="Admin User",
            email="lb-admin@example.com",
            role="admin",
            points=500,
        )

        self.login_session(high_id)
        response = self.client.get("/leaderboard")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["current_user_id"], high_id)
        self.assertEqual(
            [player["name"] for player in payload["players"]],
            ["Tie Break", "High Score", "Low Score"],
        )
        self.assertNotIn("Inactive Player", str(payload))
        self.assertNotIn("Deleted Player", str(payload))
        self.assertNotIn("Admin User", str(payload))
        self.assertNotEqual(high_id, tie_break_id)

    def test_history_page_shows_saved_result_statistics(self):
        user_id = self.create_user(name="History Player", email="history@example.com")
        self.create_result(user_id, 10)
        self.create_result(user_id, 20)
        self.create_result(user_id, 30)
        self.login_session(user_id)

        response = self.client.get("/history")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Your saved results, History Player.", page)
        self.assertRegex(page, r"Highest Score</span>\s*<h3>30</h3>")
        self.assertRegex(page, r"Latest Score</span>\s*<h3>30</h3>")
        self.assertRegex(page, r"Average Score</span>\s*<h3>20\.0</h3>")

    def test_ai_feedback_returns_service_unavailable_without_api_key(self):
        user_id = self.create_user(email="ai@example.com")
        self.login_session(user_id)

        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            response = self.client.post("/ai_feedback")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json(),
            {
                "feedback": "AI feedback is unavailable because the Gemini API key is not configured."
            },
        )


if __name__ == "__main__":
    unittest.main()
