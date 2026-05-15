import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from werkzeug.serving import make_server

from Clicking_Game import create_app
from Clicking_Game.models import database, users


try:
    from selenium import webdriver
    from selenium.common.exceptions import WebDriverException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:
    webdriver = None


class SeleniumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if webdriver is None:
            raise unittest.SkipTest("Selenium is not installed.")

        cls.temp_dir = TemporaryDirectory(ignore_cleanup_errors=True)
        test_db = Path(cls.temp_dir.name) / "selenium_test_app.sqlite"

        cls.testApp = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "selenium-test-secret-key",
                "WTF_CSRF_ENABLED": True,
                "DATABASE": str(test_db),
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{test_db}",
                "AUTO_MIGRATE": False,
            }
        )

        cls.app_context = cls.testApp.app_context()
        cls.app_context.push()

        database.Base.metadata.create_all(
            bind=cls.testApp.extensions["sqlalchemy_engine"]
        )

        cls.player_email = "selenium.player@example.com"
        cls.player_password = "Password123"

        player = users.create_user(
            name="Selenium Player",
            email=cls.player_email,
            password=cls.player_password,
            role="player",
        )

        player.email_verified = True
        database.get_session().commit()

        cls.server = make_server("127.0.0.1", 0, cls.testApp)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server_thread.join(timeout=5)

        engine = cls.testApp.extensions["sqlalchemy_engine"]

        database.SessionLocal.remove()
        database.Base.metadata.drop_all(bind=engine)
        database.SessionLocal.remove()
        engine.dispose()

        cls.app_context.pop()
        cls.temp_dir.cleanup()

    def setUp(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1200,900")

        try:
            self.driver = webdriver.Chrome(options=options)
        except WebDriverException as error:
            raise unittest.SkipTest(
                f"Chrome WebDriver could not start: {error}"
            )

        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        self.driver.quit()

    def login_as_player(self):
        self.driver.get(f"{self.base_url}/login")

        email_input = self.wait.until(
            EC.presence_of_element_located((By.ID, "email"))
        )

        password_input = self.driver.find_element(By.ID, "password")

        email_input.send_keys(self.player_email)
        password_input.send_keys(self.player_password)

        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.wait.until(EC.url_contains("/player_dashboard"))

    def test_home_page_loads(self):
        self.driver.get(self.base_url)

        self.assertIn("Egg Clicker", self.driver.title)
        self.assertIn("Build your egg empire", self.driver.page_source)

    def test_login_page_loads(self):
        self.driver.get(f"{self.base_url}/login")

        self.assertIn("Login", self.driver.title)

        email_input = self.driver.find_element(By.ID, "email")
        password_input = self.driver.find_element(By.ID, "password")

        self.assertTrue(email_input.is_displayed())
        self.assertTrue(password_input.is_displayed())

    def test_signup_page_loads_with_required_fields(self):
        self.driver.get(f"{self.base_url}/signup")

        self.assertIn("Sign Up", self.driver.title)

        self.assertTrue(self.driver.find_element(By.ID, "username").is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, "email").is_displayed())
        self.assertTrue(self.driver.find_element(By.ID, "password").is_displayed())
        self.assertTrue(
            self.driver.find_element(By.ID, "confirmPassword").is_displayed()
        )

    def test_signup_flow_displays_account_created_message(self):
        unique_email = f"selenium.signup.{uuid4().hex}@example.com"

        self.driver.get(f"{self.base_url}/signup")

        self.driver.find_element(By.ID, "username").send_keys("Selenium Signup")
        self.driver.find_element(By.ID, "email").send_keys(unique_email)
        self.driver.find_element(By.ID, "password").send_keys("Password123")
        self.driver.find_element(By.ID, "confirmPassword").send_keys("Password123")

        self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.TAG_NAME, "body"),
                "Account created",
            )
        )

        self.assertIn("Account created", self.driver.page_source)

    def test_valid_login_redirects_to_player_dashboard(self):
        self.login_as_player()

        self.assertIn("/player_dashboard", self.driver.current_url)
        self.assertIn("Player Dashboard", self.driver.page_source)
        self.assertIn("Selenium Player", self.driver.page_source)

    def test_start_game_button_redirects_to_game_page(self):
        self.login_as_player()

        start_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, "startGameBtn"))
        )

        start_button.click()

        self.wait.until(EC.url_contains("/game"))

        self.assertIn("/game", self.driver.current_url)
        self.assertIn("Clicker Game", self.driver.page_source)

    def _seed_leaderboard_player(self, name, email, points):
        """Helper: create a verified player with a GameState row carrying a score."""
        db_session = database.get_session()

        player = users.create_user(
            name=name,
            email=email,
            password="Password123",
            role="player",
        )

        if player is None:
            # Already created by an earlier test in the same class run
            player = users.get_by_email(email)

        player.email_verified = True

        existing_state = (
            db_session.query(users.GameState).filter_by(user_id=player.id).first()
        )

        if existing_state:
            existing_state.points = points
        else:
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

        return player

    def test_leaderboard_displays_player_rows_on_game_page(self):
        """Leaderboard panel renders with seeded players on /game."""
        self._seed_leaderboard_player(
            "Selenium Alice", "selenium.alice@example.com", 800
        )
        self._seed_leaderboard_player(
            "Selenium Bob", "selenium.bob@example.com", 400
        )

        self.driver.get(f"{self.base_url}/game")

        # Leaderboard panel header is visible
        self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//div[contains(@class, 'card-header') "
                    "and normalize-space(text())='Leaderboard']",
                )
            )
        )

        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "ul.list-group .list-group-item"
        )

        self.assertGreaterEqual(
            len(rows),
            2,
            "Leaderboard should show at least the two seeded players",
        )

        page = self.driver.page_source

        self.assertIn("Selenium Alice", page)
        self.assertIn("Selenium Bob", page)

    def test_leaderboard_highlights_current_user_row(self):
        """Logged-in user's leaderboard row gets the leaderboard-self class and a 'You' badge."""
        # Give the seeded selenium player a high score so they appear at the top
        seeded_player = users.get_by_email(self.player_email)
        self._seed_leaderboard_player(
            seeded_player.name, self.player_email, 5000
        )

        self.login_as_player()
        self.driver.get(f"{self.base_url}/game")

        self_row = self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "li.leaderboard-self")
            )
        )

        self.assertIn(seeded_player.name, self_row.text)
        self.assertIn("You", self_row.text)


if __name__ == "__main__":
    unittest.main()