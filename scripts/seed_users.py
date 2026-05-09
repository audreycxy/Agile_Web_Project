#!/usr/bin/env python
# Command-line script for creating default admin and player accounts

from pathlib import Path
import sys

# Add the project root directory to the Python path so project modules can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Clicking_Game import create_app
from Clicking_Game.models import users


# Default user accounts used to initialise the database
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
    # Create the Flask app context and insert default users if they do not already exist
    app = create_app()
    created = 0

    with app.app_context():
        for user_data in DEFAULT_USERS:
            existing_user = users.get_by_email(user_data["email"])

            # Skip users that already exist to avoid duplicate accounts
            if existing_user is not None:
                print(f"Skipped existing user: {existing_user.email}")
                continue

            user = users.create_user(**user_data)
            created += 1
            print(f"Created {user.role} user: {user.email}")

    # Display the number of new users created
    print(f"Seed complete. Created {created} user(s).")


if __name__ == "__main__":
    # Run the seed function when this file is executed directly
    seed_users()