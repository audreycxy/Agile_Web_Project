#!/usr/bin/env python
# Creates a custom user form the command line
import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Clicking_Game import create_app
from Clicking_Game.models import users

def parse_args():
    parser = argparse.ArgumentParser(description="Add a user to the Clicking Game database.")
    parser.add_argument("--name", required=True, help="Display name for the user.")
    parser.add_argument("--email", required=True, help="Unique login email address.")
    parser.add_argument("--password", required=True, help="Login password to hash and store.")
    parser.add_argument(
        "--role",
        choices=("admin", "player"),
        default="player",
        help="User role. Defaults to player.",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    app = create_app()

    with app.app_context():
        user = users.create_user(
            name=args.name,
            email=args.email,
            password=args.password,
            role=args.role,
        )

    if user is None:
        print(f"User already exists: {args.email.strip().lower()}", file=sys.stderr)
        return 1

    print(f"Created {user.role} user: {user.email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
