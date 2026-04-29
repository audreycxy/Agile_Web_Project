# Defining database tables and user-related helper functions
from __future__ import annotations
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash
from .database import Base, get_session

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
    )
    user.set_password(password)

    try:
        session.add(user)
        session.commit()
    except IntegrityError:
        session.rollback()
        return None

    return user

# Authenticates a user by email and password, returning the user if valid
def authenticate(email, password):
    user = get_by_email(email)

    if user is None:
        return None

    if not user.check_password(password):
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
