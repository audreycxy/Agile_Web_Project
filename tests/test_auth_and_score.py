from Clicking_Game.models import database, users
from conftest import create_verified_user


def login(client, email="player@example.com", password="Password123"):
    return client.post(
        "/login",
        data={
            "email": email,
            "password": password,
        },
        follow_redirects=False,
    )


def test_signup_with_valid_user_details(client):
    response = client.post(
        "/signup",
        data={
            "username": "New Player",
            "email": "newplayer@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    assert b"Account created" in response.data

    created_user = users.get_by_email("newplayer@example.com")
    assert created_user is not None
    assert created_user.name == "New Player"
    assert created_user.role == "player"


def test_login_with_valid_account_details_redirects_player(client):
    create_verified_user(
        name="Player User",
        email="player@example.com",
        password="Password123",
        role="player",
    )

    response = login(client)

    assert response.status_code == 302
    assert "/player_dashboard" in response.headers["Location"]


def test_login_with_invalid_account_details(client):
    response = login(
        client,
        email="wrong@example.com",
        password="WrongPassword",
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_player_role_redirects_to_player_dashboard(client):
    create_verified_user(
        name="Player User",
        email="player@example.com",
        password="Password123",
        role="player",
    )

    response = login(client, email="player@example.com", password="Password123")

    assert response.status_code == 302
    assert "/player_dashboard" in response.headers["Location"]


def test_admin_role_redirects_to_admin_dashboard(client):
    create_verified_user(
        name="Admin User",
        email="admin@example.com",
        password="Password123",
        role="admin",
    )

    response = login(client, email="admin@example.com", password="Password123")

    assert response.status_code == 302
    assert "/admin_dashboard" in response.headers["Location"]


def test_player_cannot_access_admin_dashboard(client):
    create_verified_user(
        name="Player User",
        email="player@example.com",
        password="Password123",
        role="player",
    )

    login(client, email="player@example.com", password="Password123")

    response = client.get("/admin_dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_admin_cannot_access_player_dashboard(client):
    create_verified_user(
        name="Admin User",
        email="admin@example.com",
        password="Password123",
        role="admin",
    )

    login(client, email="admin@example.com", password="Password123")

    response = client.get("/player_dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logged_in_player_can_save_score(client):
    player = create_verified_user(
        name="Score Player",
        email="scoreplayer@example.com",
        password="Password123",
        role="player",
    )

    login(client, email="scoreplayer@example.com", password="Password123")

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

    response = client.post("/api/sync", json={}, follow_redirects=False)

    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "success"
    assert data["new_points"] >= 1

    saved_results = users.list_results(user_id=player.id)

    assert len(saved_results) == 1
    assert saved_results[0].score == data["new_points"]


def test_guest_user_cannot_save_score(client):
    response = client.post("/api/sync", json={}, follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    saved_results = users.list_results()
    assert saved_results == []

def test_player_dashboard_displays_highest_egg(client):
    create_verified_user(
        name="Dashboard Player",
        email="dashboard@example.com",
        password="Password123",
        role="player",
    )

    login(client, email="dashboard@example.com", password="Password123")

    response = client.get("/player_dashboard")

    assert response.status_code == 200
    assert b"Highest Egg" in response.data
    assert b"Standard" in response.data