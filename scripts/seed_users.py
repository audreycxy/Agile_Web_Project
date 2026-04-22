#!/usr/bin/env python
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Clicking_Game import create_app
from Clicking_Game.models import users

DEFAULT_USERS = (
    {
        "email": "admin@example.com",
        "name": "Admin User",
        "password": "admin123",
        "role": "admin",
    },
    {
        "email": "player@example.com",
        "name": "Player User",
        "password": "player123",
        "role": "player",
    },
)


def seed_users():
    app = create_app()
    created = 0

    with app.app_context():
        for user_data in DEFAULT_USERS:
            existing_user = users.get_by_email(user_data["email"])
            if existing_user is not None:
                print(f"Skipped existing user: {existing_user.email}")
                continue

            user = users.create_user(**user_data)
            created += 1
            print(f"Created {user.role} user: {user.email}")

    print(f"Seed complete. Created {created} user(s).")


if __name__ == "__main__":
    seed_users()
