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
from Clicking_Game.models.database import get_session


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
    updated = 0

    with app.app_context():
        session = get_session()

        for user_data in DEFAULT_USERS:
            existing_user = users.get_by_email(user_data["email"])

            # If the default user already exists, restore the expected seed state so
            # the documented credentials keep working across local resets and schema changes.
            if existing_user is not None:
                existing_user.name = user_data["name"]
                existing_user.role = user_data["role"]
                existing_user.is_active = True
                existing_user.set_password(user_data["password"])
                existing_user.email_verified = True
                existing_user.email_verification_token = None
                updated += 1
                print(f"Updated existing seeded user: {existing_user.email}")
                continue

            user = users.create_user(**user_data)

            # Seeded users are trusted default accounts, so they should be email-verified
            user.email_verified = True
            user.email_verification_token = None

            created += 1
            print(f"Created verified {user.role} user: {user.email}")

        session.commit()

    # Display the number of new users created and existing users updated
    print(f"Seed complete. Created {created} user(s), updated {updated} user(s).")


if __name__ == "__main__":
    # Run the seed function when this file is executed directly
    seed_users()
