# Command-line helper for creating a secure admin account.
# This script is intended for deployment or production-like setup.
# It avoids hard-coded admin credentials by asking for account details
# interactively or reading them from environment variables.

import os
import sys
from getpass import getpass

from Clicking_Game import create_app
from Clicking_Game.models import database, users


def get_value(env_name, prompt_text, secret=False):
    # Read a value from an environment variable or prompt the user.
    # Password values can be entered with getpass so they are not displayed
    # in the terminal while being typed.
    value = os.environ.get(env_name)

    if value:
        return value.strip()

    if secret:
        return getpass(prompt_text).strip()

    return input(prompt_text).strip()


def main():
    # Create a verified admin account using secure user-provided credentials.
    # The script refuses to overwrite an existing account with the same email,
    # which prevents accidental password replacement or unsafe credential reuse.
    app = create_app()

    with app.app_context():
        name = get_value("ADMIN_NAME", "Admin name: ")
        email = get_value("ADMIN_EMAIL", "Admin email: ").lower()
        password = get_value("ADMIN_PASSWORD", "Admin password: ", secret=True)

        if not name or not email or not password:
            print("Admin name, email, and password are required.")
            sys.exit(1)

        existing_user = users.get_by_email(email)

        if existing_user is not None:
            print("An account with this email already exists.")
            print("For safety, this script does not overwrite existing passwords.")
            sys.exit(1)

        admin_user = users.create_user(
            name=name,
            email=email,
            password=password,
            role="admin",
        )

        if admin_user is None:
            print("Admin account could not be created.")
            sys.exit(1)

        # Deployment-created admin accounts should be immediately usable.
        admin_user.email_verified = True
        admin_user.email_verification_token = None

        db_session = database.get_session()
        db_session.commit()

        print("Admin account created successfully.")
        print("Use the configured admin email and password to log in.")


if __name__ == "__main__":
    main()