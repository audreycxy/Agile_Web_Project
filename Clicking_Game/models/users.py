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
    game_state: Mapped["GameState"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    # is_active = admin Whether to disable the account
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        index=True,
        nullable=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="0",
        index=True,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    points: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    current_infinity_level: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    current_type: Mapped[str] = mapped_column(
        String(50),
        default="standard",
        server_default="standard",
        nullable=False,
    )
    highest_type: Mapped[str] = mapped_column(
        String(50),
        default="standard",
        server_default="standard",
        nullable=False,
    )
    clicks_remaining: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    progress_percent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
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

    # avatar_filename = the basename of the user's uploaded avatar image,
    # stored under instance/uploads/avatars/. None means "no avatar uploaded,
    # show the default fallback image instead".
    avatar_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    # active_session_token enforces single-session login. On each successful
    # /login we rotate this to a fresh random value and store the new value
    # in the user's session cookie. The before_request hook compares the two
    # on every request, and if they no longer match (because someone else
    # logged in from another device and rotated the token), it boots the
    # stale session back to /login. None means "currently logged out".
    active_session_token: Mapped[str | None] = mapped_column(
        String(255),
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

# Game state table
class GameState(Base):
    __tablename__ = "game_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )

    points: Mapped[int] = mapped_column(Integer, default=0)
    current_infinity_level: Mapped[int] = mapped_column(Integer, default=0)
    current_type: Mapped[str] = mapped_column(String(50), default="standard")
    highest_type: Mapped[str] = mapped_column(String(50), default="standard")
    clicks_remaining: Mapped[int | None] = mapped_column(Integer)

    click_power_lvl: Mapped[int] = mapped_column(Integer, default=1)
    autoclicker_lvl: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="game_state")

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

# Verify function. Returns the freshly-verified User on success, or None if
# the token does not match any user (e.g. expired, already-used, typo). The
# caller can use the returned user to start a logged-in session right away.
def verify_email_token(token):
    session = get_session()
    user = get_by_verification_token(token)

    if user is None:
        return None

    user.email_verified = True
    user.email_verification_token = None
    session.commit()
    return user


# Generates a fresh random token, stores it on the user row, and returns it
# so the caller can put it in the new session cookie. Called on every
# successful login; this overwrites any previous token, which is what
# invalidates any earlier session (the older cookie's token no longer
# matches the row).
def issue_active_session_token(user_id):
    session = get_session()
    user = session.get(User, user_id)

    if user is None:
        return None

    token = secrets.token_urlsafe(32)
    user.active_session_token = token
    session.commit()
    return token


# Wipes the token, explicitly invalidating the current session. Called on
# logout. Without this, an old cookie could remain valid until the user
# logs in somewhere else and rotates the token.
def clear_active_session_token(user_id):
    if user_id is None:
        return False

    session = get_session()
    user = session.get(User, user_id)

    if user is None:
        return False

    user.active_session_token = None
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

    if user.is_deleted:
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


def list_leaderboard(limit=10):
    session = get_session()
    stmt = (
        select(User)
        .join(GameState)
        .where(
            User.role == "player",
            User.is_active.is_(True),
            User.is_deleted.is_(False),
        )
        .order_by(
            GameState.points.desc(),
            GameState.current_infinity_level.desc(),
            User.id.asc(),
        )
        .limit(limit)
    )

    return session.scalars(stmt).all()


def list_player_progress(search=None, limit=None, sort_by="points"):
    session = get_session()
    stmt = select(User).where(User.role == "player", User.is_deleted.is_(False))

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where((User.name.ilike(term)) | (User.email.ilike(term)))

    if sort_by == "updated":
        stmt = stmt.order_by(User.updated_at.desc(), User.points.desc(), User.id.desc())
    else:
        stmt = stmt.order_by(
            User.points.desc(),
            User.current_infinity_level.desc(),
            User.updated_at.desc(),
            User.id.asc(),
        )

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

    if user.is_deleted:
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

    if user.is_deleted:
        return False

    user.is_active = bool(is_active)
    if not user.is_active:
        user.active_session_token = None
    session.commit()
    return True


def soft_delete_user(user):
    session = get_session()

    if user is None or user.is_deleted:
        return False

    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    user.active_session_token = None
    session.commit()
    return True

def create_game_result(user_id, score, duration_seconds=None):
    session = get_session()

    result = GameResult(
        user_id=user_id,
        score=score,
        duration_seconds=duration_seconds,
    )

    session.add(result)
    session.commit()

    return result

def update_user_game_state(
    user_id,
    points,
    current_infinity_level,
    current_type,
    highest_type,
    clicks_remaining,
    progress_percent,
):
    session = get_session()
    user = session.get(User, user_id)

    if user is None:
        return None

    user.points = points
    user.current_infinity_level = current_infinity_level
    user.current_type = current_type
    user.highest_type = highest_type
    user.clicks_remaining = clicks_remaining
    user.progress_percent = progress_percent

    session.commit()
    return user


def reset_user_game_state(user_id):
    session = get_session()
    user = session.get(User, user_id)

    if user is None:
        return None

    # Reset the legacy User-row copies. Some admin reports still read from
    # these fields, so we keep them in sync with the live state.
    user.points = 0
    user.current_infinity_level = 0
    user.current_type = "standard"
    user.highest_type = "standard"
    user.clicks_remaining = None
    user.progress_percent = 0

    # Reset the live GameState row, which is what the in-game UI actually
    # reads on /game. Without this, the reset above would be invisible to
    # the player after they click "Restart Progress".
    if user.game_state is not None:
        user.game_state.points = 0
        user.game_state.current_infinity_level = 0
        user.game_state.current_type = "standard"
        user.game_state.highest_type = "standard"
        user.game_state.clicks_remaining = None
        user.game_state.click_power_lvl = 1
        user.game_state.autoclicker_lvl = 0

    session.commit()
    return user
