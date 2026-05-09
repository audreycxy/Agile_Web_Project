# Defining database tables and user-related helper functions
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from .database import Base, get_session
import secrets

# User table
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'player')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        default="player",
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    results: Mapped[list["GameResult"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    # is_active = admin Whether to disable the account
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        index=True,
        nullable=False,
    )

    # email_verified = Has the user completed the email verification
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        index=True,
        nullable=False,
    )

    email_verification_token: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=True,
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Game result table
class GameResult(Base):
    __tablename__ = "game_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User | None] = relationship(back_populates="results")

# HELPER FUNCTIONS
# Strips spaces and lowercase email 
def normalize_email(email):
    return email.strip().lower()

# Finds a user by email
def get_by_email(email):
    normalized_email = normalize_email(email)
    if not normalized_email:
        return None

    return get_session().scalar(select(User).where(User.email == normalized_email))

# Finds a user by ID
def get_by_id(user_id):
    if user_id is None:
        return None

    return get_session().get(User, user_id)

# Creates a new user with the given details
def create_user(name, email, password, role="player"):
    session = get_session()
    user = User(
        email=normalize_email(email),
        name=name.strip(),
        role=role,
        is_active=True,
        email_verified=False,
        email_verification_token=secrets.token_urlsafe(32),
    )
    user.set_password(password)

    try:
        session.add(user)
        session.commit()
    except IntegrityError:
        session.rollback()
        return None

    return user

# Find the user's function through tokens
def get_by_verification_token(token):
    if not token:
        return None

    return get_session().scalar(
        select(User).where(User.email_verification_token == token)
    )

# Verify function
def verify_email_token(token):
    session = get_session()
    user = get_by_verification_token(token)

    if user is None:
        return False

    user.email_verified = True
    user.email_verification_token = None
    session.commit()
    return True

# Updates a user's name/email/password; returns False on duplicate-email conflict
def update_profile(user, name=None, email=None, password=None):
    session = get_session()
    if name is not None:
        user.name = name.strip()
    if email is not None:
        user.email = normalize_email(email)
    if password:
        user.set_password(password)
    try:
        session.commit()
        return True
    except IntegrityError:
        session.rollback()
        return False

# Authenticates a user by email and password, returning the user if valid
# Prevent unverified users from logging in
def authenticate(email, password):
    user = get_by_email(email)

    if user is None:
        return None

    if not user.check_password(password):
        return None
    
    if not user.is_active:
        return None

    if not user.email_verified:
        return None
    
    return user

# Lists users for admin pages
def list_users(search=None, role=None):
    session = get_session()
    stmt = select(User).order_by(User.created_at.desc(), User.id.desc())

    if role in {"admin", "player"}:
        stmt = stmt.where(User.role == role)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where((User.name.ilike(term)) | (User.email.ilike(term)))

    return session.scalars(stmt).all()

# Lists saved game results for admin/player pages
def list_results(search=None, user_id=None, limit=None):
    session = get_session()
    stmt = select(GameResult).order_by(GameResult.created_at.desc(), GameResult.id.desc())

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.join(GameResult.user).where(
            (User.name.ilike(term)) | (User.email.ilike(term))
        )

    if user_id is not None:
        stmt = stmt.where(GameResult.user_id == user_id)

    if limit is not None:
        stmt = stmt.limit(limit)

    return session.scalars(stmt).all()

# Updates a user's role from the admin account management page
def update_user_role(user_id, new_role):
    if new_role not in {"admin", "player"}:
        return False

    session = get_session()
    user = session.get(User, user_id)

    if user is None:
        return False

    user.role = new_role
    session.commit()
    return True

# Activates or inactivates a user account from the admin account management page
def set_user_active(user_id, is_active):
    session = get_session()
    user = session.get(User, user_id)

    if user is None:
        return False

    user.is_active = bool(is_active)
    session.commit()
    return True